# -*- coding: utf-8 -*-
"""
程式碼執行工具：讓 Agent 在 Docker Sandbox 中執行 Python 程式碼
"""

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.modules.sandbox.schemas import CodeExecutionRequest, InputFile
from app.modules.sandbox.service import SandboxService


def create_execute_python_tool(sandbox_service: SandboxService):
    """
    建立程式碼執行工具（工廠函數）

    使用工廠函數而非直接定義 @tool，是為了注入 sandbox_service 依賴。
    輸入檔案透過 RunnableConfig 的 configurable.input_files 傳遞，
    確保並行執行時不會互相干擾。

    Args:
        sandbox_service: SandboxService 實例

    Returns:
        LangChain Tool
    """

    @tool(response_format="content_and_artifact")
    async def execute_python(code: str, config: RunnableConfig) -> tuple[str, dict]:
        """在安全的 Docker Sandbox 環境中執行 Python 程式碼。

        Sandbox 環境已預裝以下套件：pandas, numpy, matplotlib, requests, openpyxl。
        程式碼在隔離容器中執行，有 CPU、記憶體和時間限制。

        如果需要產生圖表或檔案，請將檔案儲存到 /workspace/output/ 目錄。
        如果使用者上傳了檔案，檔案位於 /workspace/input/ 目錄。

        Args:
            code: 要執行的 Python 程式碼

        Returns:
            執行結果，包含標準輸出和錯誤資訊
        """
        # 從 RunnableConfig 取得輸入檔案（並行安全）
        input_files_data = config.get("configurable", {}).get("input_files", [])
        request = CodeExecutionRequest(
            code=code,
            input_files=[
                InputFile(
                    host_path=f["file_path"],
                    filename=f["original_filename"],
                )
                for f in input_files_data
            ],
        )
        result = await sandbox_service.execute(request)

        # 格式化結果為文字（給 LLM 閱讀）
        parts = []

        if result.success:
            parts.append("✅ 執行成功")
        else:
            parts.append("❌ 執行失敗")

        if result.stdout:
            parts.append(f"標準輸出:\n{result.stdout}")

        if result.stderr:
            parts.append(f"標準錯誤:\n{result.stderr}")

        if result.error_message:
            parts.append(f"錯誤訊息: {result.error_message}")

        if result.output_files:
            file_names = [f.filename for f in result.output_files]
            parts.append(f"輸出檔案: {', '.join(file_names)}")

        parts.append(f"執行時間: {result.execution_time:.2f}s")

        artifact = {
            "success": result.success,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "output_files": [
                output_file.model_dump() for output_file in result.output_files
            ],
        }

        return "\n\n".join(parts), artifact

    return execute_python
