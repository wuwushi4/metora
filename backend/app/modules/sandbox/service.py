# -*- coding: utf-8 -*-
"""
Sandbox 服務：透過 Docker 容器安全執行 Python 程式碼

使用 put_archive / get_archive（docker cp 等效）來傳輸檔案，
避免 Docker-in-Docker 環境下 bind mount 路徑不一致的問題。
"""
import asyncio
import base64
import io
import mimetypes
import tarfile
import time
from typing import Optional

import aiodocker
from loguru import logger

from app.modules.sandbox.schemas import (
    CodeExecutionRequest,
    CodeExecutionResult,
    InputFile,
    OutputFile,
)


class SandboxService:
    """
    Docker Sandbox 服務

    透過建立短生命週期的 Docker 容器來安全執行 Python 程式碼。
    每次執行建立一個新容器，執行完畢後自動清理。

    檔案傳輸使用 Docker API 的 put_archive / get_archive，
    兼容 Docker-in-Docker（DinD）環境。
    """

    def __init__(self, settings):
        self.settings = settings
        self._docker: Optional[aiodocker.Docker] = None

    async def _get_docker(self) -> aiodocker.Docker:
        """取得 Docker 客戶端（延遲初始化）"""
        if self._docker is None:
            self._docker = aiodocker.Docker()
        return self._docker

    async def execute(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """
        在 Docker 容器中執行 Python 程式碼

        流程：
        1. 建立容器（不使用 bind mount）
        2. 透過 put_archive 將程式碼注入容器的 /workspace/
        3. 啟動容器並等待完成
        4. 透過 get_archive 從容器的 /workspace/output/ 取回輸出檔案
        5. 清理容器
        """
        start_time = time.monotonic()
        container = None

        try:
            docker = await self._get_docker()

            # 準備容器配置（無 bind mount）
            timeout = min(request.timeout, self.settings.SANDBOX_TIMEOUT)
            container_config = self._build_container_config(timeout=timeout)

            # 建立容器
            container = await docker.containers.create_or_replace(
                name=None,
                config=container_config,
            )

            # 透過 put_archive 注入程式碼到 /workspace/
            code_tar = self._create_code_tar(request.code)
            await container.put_archive(path="/workspace", data=code_tar)

            # 注入輸入檔案到 /workspace/input/
            if request.input_files:
                input_tar = self._create_input_files_tar(request.input_files)
                if input_tar:
                    await container.put_archive(path="/workspace", data=input_tar)

            # 啟動容器
            await container.start()

            logger.debug(
                "Sandbox 容器已啟動",
                extra={"container_id": container.id[:12]},
            )

            # 等待容器完成（帶超時）
            try:
                async with asyncio.timeout(timeout + 5):
                    await container.wait()
            except asyncio.TimeoutError:
                try:
                    await container.kill()
                except Exception:
                    pass
                return CodeExecutionResult(
                    success=False,
                    stderr="",
                    exit_code=-1,
                    execution_time=time.monotonic() - start_time,
                    error_message=f"執行超時（超過 {timeout} 秒）",
                )

            # 取得容器輸出
            stdout_logs = await container.log(stdout=True)
            stderr_logs = await container.log(stderr=True)

            stdout = "".join(stdout_logs)
            stderr = "".join(stderr_logs)

            # 取得退出碼
            container_info = await container.show()
            exit_code = container_info["State"].get("ExitCode", -1)

            # 截斷過長的輸出
            max_output = self.settings.SANDBOX_MAX_OUTPUT_SIZE
            if len(stdout) > max_output:
                stdout = stdout[:max_output] + "\n... (輸出已截斷)"
            if len(stderr) > max_output:
                stderr = stderr[:max_output] + "\n... (輸出已截斷)"

            # 透過 get_archive 取回輸出檔案
            output_files = await self._collect_output_files_from_container(
                container, max_output
            )

            execution_time = time.monotonic() - start_time

            logger.debug(
                "Sandbox 執行完成",
                extra={
                    "container_id": container.id[:12],
                    "exit_code": exit_code,
                    "execution_time": f"{execution_time:.2f}s",
                    "stdout_length": len(stdout),
                    "stderr_length": len(stderr),
                    "output_files_count": len(output_files),
                },
            )

            return CodeExecutionResult(
                success=exit_code == 0,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                output_files=output_files,
                execution_time=execution_time,
            )

        except aiodocker.exceptions.DockerError as e:
            execution_time = time.monotonic() - start_time
            logger.error(f"Sandbox Docker 錯誤: {e}", exc_info=True)
            return CodeExecutionResult(
                success=False,
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                error_message=f"Docker 錯誤: {e}",
            )

        except Exception as e:
            execution_time = time.monotonic() - start_time
            logger.error(f"Sandbox 執行異常: {e}", exc_info=True)
            return CodeExecutionResult(
                success=False,
                stderr=str(e),
                exit_code=-1,
                execution_time=execution_time,
                error_message=f"系統錯誤: {type(e).__name__}: {e}",
            )

        finally:
            if container:
                try:
                    await container.delete(force=True)
                except Exception:
                    pass

    def _build_container_config(self, timeout: int) -> dict:
        """建立 Docker 容器配置（無 bind mount）"""
        config = {
            "Image": self.settings.SANDBOX_IMAGE,
            "Cmd": ["python", "-u", "/workspace/main.py"],
            "WorkingDir": "/workspace",
            "NetworkDisabled": not self.settings.SANDBOX_NETWORK_ENABLED,
            "HostConfig": {
                "Memory": self._parse_memory_limit(
                    self.settings.SANDBOX_MEMORY_LIMIT
                ),
                "NanoCpus": int(self.settings.SANDBOX_CPU_LIMIT * 1e9),
                "PidsLimit": 100,
                "ReadonlyRootfs": False,
                "AutoRemove": False,
                "SecurityOpt": ["no-new-privileges"],
            },
            "StopTimeout": timeout,
        }

        if self.settings.SANDBOX_NETWORK_ENABLED and self.settings.SANDBOX_NETWORK_NAME:
            config["HostConfig"]["NetworkMode"] = self.settings.SANDBOX_NETWORK_NAME

        return config

    @staticmethod
    def _create_code_tar(code: str) -> bytes:
        """將 Python 程式碼打包為 tar archive（用於 put_archive）"""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            code_bytes = code.encode("utf-8")
            info = tarfile.TarInfo(name="main.py")
            info.size = len(code_bytes)
            tar.addfile(info, io.BytesIO(code_bytes))
        buf.seek(0)
        return buf.read()

    @staticmethod
    def _create_input_files_tar(input_files: list[InputFile]) -> Optional[bytes]:
        """
        將輸入檔案打包為 tar archive，注入到容器的 /workspace/input/ 目錄

        Args:
            input_files: InputFile 列表（含 host_path 和 filename）

        Returns:
            tar archive bytes，若無有效檔案則返回 None
        """
        import os

        buf = io.BytesIO()
        files_added = 0

        with tarfile.open(fileobj=buf, mode="w") as tar:
            for input_file in input_files:
                if not os.path.exists(input_file.host_path):
                    logger.warning(f"輸入檔案不存在，跳過: {input_file.host_path}")
                    continue

                # 使用原始檔名放入 input/ 子目錄
                arcname = f"input/{input_file.filename}"

                try:
                    tar.add(input_file.host_path, arcname=arcname)
                    files_added += 1
                    logger.debug(f"注入輸入檔案到容器: {arcname}")
                except Exception as e:
                    logger.warning(f"打包輸入檔案失敗: {input_file.host_path} - {e}")

        if files_added == 0:
            return None

        buf.seek(0)
        return buf.read()

    @staticmethod
    def _parse_memory_limit(limit_str: str) -> int:
        """將記憶體限制字串轉換為 bytes（例如 '512m' -> 536870912）"""
        limit_str = limit_str.strip().lower()
        if limit_str.endswith("g"):
            return int(float(limit_str[:-1]) * 1024 * 1024 * 1024)
        elif limit_str.endswith("m"):
            return int(float(limit_str[:-1]) * 1024 * 1024)
        elif limit_str.endswith("k"):
            return int(float(limit_str[:-1]) * 1024)
        return int(limit_str)

    async def _collect_output_files_from_container(
        self, container, max_total_size: int
    ) -> list[OutputFile]:
        """透過 get_archive 從容器中收集 /workspace/output/ 的檔案"""
        output_files = []
        total_size = 0

        try:
            # aiodocker 0.26 的 get_archive 直接回傳 tarfile.TarFile
            tar = await container.get_archive("/workspace/output/")

            for member in tar.getmembers():
                if not member.isfile():
                    continue

                if total_size + member.size > max_total_size:
                    logger.warning(
                        f"輸出檔案總大小超過限制，跳過: {member.name}"
                    )
                    break

                try:
                    f = tar.extractfile(member)
                    if f is None:
                        continue
                    content_bytes = f.read()
                    content_base64 = base64.b64encode(
                        content_bytes
                    ).decode("ascii")

                    # member.name 可能是 "output/xxx.png"，取檔名部分
                    filename = member.name.split("/")[-1]
                    if not filename:
                        continue

                    mime_type = (
                        mimetypes.guess_type(filename)[0]
                        or "application/octet-stream"
                    )

                    output_files.append(
                        OutputFile(
                            filename=filename,
                            content_base64=content_base64,
                            mime_type=mime_type,
                            size=member.size,
                        )
                    )
                    total_size += member.size
                except Exception as e:
                    logger.warning(
                        f"讀取容器輸出檔案失敗: {member.name} - {e}"
                    )

            tar.close()

        except aiodocker.exceptions.DockerError as e:
            # 如果 /workspace/output/ 不存在或為空，get_archive 會報 404
            if "404" in str(e) or "No such" in str(e):
                logger.debug("容器中沒有輸出檔案目錄")
            else:
                logger.warning(f"從容器取回輸出檔案失敗: {e}")
        except Exception as e:
            logger.warning(f"收集容器輸出檔案異常: {e}")

        return output_files

    async def close(self) -> None:
        """關閉 Docker 客戶端連線"""
        if self._docker:
            await self._docker.close()
            self._docker = None

    async def health_check(self) -> bool:
        """檢查 Sandbox 服務是否可用"""
        try:
            docker = await self._get_docker()
            await docker.images.inspect(self.settings.SANDBOX_IMAGE)
            return True
        except Exception as e:
            logger.warning(f"Sandbox 健康檢查失敗: {e}")
            return False
