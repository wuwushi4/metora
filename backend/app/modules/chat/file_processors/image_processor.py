"""
圖片處理器 - 支援壓縮、格式轉換和安全驗證
"""

import base64
import imghdr
from loguru import logger
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

from .base import BaseFileProcessor
from .exceptions import FileValidationError, FileProcessingError, FileSizeExceededError




class ImageProcessor(BaseFileProcessor):
    """
    圖片處理器

    功能:
    - 驗證圖片格式和大小
    - Magic Number 驗證 (防止偽造副檔名)
    - 圖片壓縮和尺寸調整
    - 轉換為 JPEG 格式
    - Base64 編碼供 LLM 使用
    """

    # 允許的圖片格式
    ALLOWED_FORMATS = {"jpeg", "png", "gif", "webp", "bmp"}

    # 允許的 MIME 類型
    MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
    }

    async def validate(self, file: UploadFile) -> None:
        """
        驗證圖片

        檢查項目:
        1. 檔案大小
        2. MIME 類型
        3. Magic Number (真實格式驗證)
        """
        # 1. 檔案大小驗證
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # 重置指針

        max_size = self.settings.CHAT_IMAGE_MAX_SIZE
        if file_size > max_size:
            raise FileSizeExceededError(file_size, max_size, file.filename)

        # 2. MIME 類型驗證
        if file.content_type not in self.MIME_TYPES:
            raise FileValidationError(
                f"不支援的圖片 MIME 類型: {file.content_type}",
                details={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "supported": list(self.MIME_TYPES),
                },
            )

        # 3. Magic Number 驗證 (檢測真實格式)
        await self._validate_file_header(file)

    async def _validate_file_header(self, file: UploadFile) -> None:
        """
        使用 imghdr 驗證圖片格式 (Magic Number)

        防止使用者偽造副檔名上傳惡意檔案。
        """
        # 讀取前 512 bytes 用於格式檢測
        header = await file.read(512)
        file.file.seek(0)  # 重置指針

        # 使用 imghdr 檢測真實格式
        detected_format = imghdr.what(None, h=header)

        if detected_format not in self.ALLOWED_FORMATS:
            raise FileValidationError(
                f"圖片格式驗證失敗 (偵測到: {detected_format})",
                details={
                    "filename": file.filename,
                    "detected_format": detected_format,
                    "allowed_formats": list(self.ALLOWED_FORMATS),
                },
            )

    async def process(self, file: UploadFile, save_dir: Path) -> Dict[str, Any]:
        """
        處理並儲存圖片

        流程:
        1. 驗證檔案
        2. 讀取圖片
        3. 壓縮 (如果啟用)
        4. 轉換為 JPEG
        5. 儲存到磁碟
        6. 返回附件資訊
        """
        # 1. 驗證
        await self.validate(file)

        # 2. 讀取圖片（直接從 file.file 讀取，避免額外記憶體佔用）
        img = Image.open(file.file)
        file.file.seek(0)  # 重置指針供後續使用

        # 取得原始尺寸
        original_width, original_height = img.size

        # 3. 壓縮處理 (如果啟用)
        if self.settings.CHAT_IMAGE_COMPRESS_ENABLED:
            img = await self._compress_image(img)

        # 4. 生成唯一檔名並儲存
        filename = self._generate_safe_filename(file.filename)
        # 強制使用 .jpg 副檔名
        filename = Path(filename).stem + ".jpg"
        save_path = self._get_storage_path(filename, save_dir)

        # 5. 轉換 RGBA → RGB (for JPEG)
        if img.mode == "RGBA":
            # 創建白色背景
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])  # 使用 alpha 通道作為遮罩
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 6. 儲存為 JPEG
        img.save(
            save_path,
            "JPEG",
            quality=self.settings.CHAT_IMAGE_QUALITY,
            optimize=True,
        )

        # 取得壓縮後的檔案大小和尺寸
        file_size = save_path.stat().st_size
        compressed_width, compressed_height = img.size

        logger.info(
            f"圖片處理完成: {file.filename} -> {filename}",
            extra={
                "compressed_size": file_size,
                "original_dimensions": f"{original_width}x{original_height}",
                "compressed_dimensions": f"{compressed_width}x{compressed_height}",
            },
        )

        # 7. 返回附件資訊
        attachment_id = str(uuid4())
        return {
            "id": attachment_id,
            "type": "image",
            "file_path": str(save_path),
            "original_filename": file.filename,
            "file_size": file_size,
            "mime_type": "image/jpeg",
            "extra_data": {
                "width": compressed_width,
                "height": compressed_height,
                "original_width": original_width,
                "original_height": original_height,
            }
        }

    async def _compress_image(self, img: Image.Image) -> Image.Image:
        """
        壓縮圖片 (等比例縮放)

        Args:
            img: PIL Image 物件

        Returns:
            壓縮後的 Image 物件
        """
        max_width = self.settings.CHAT_IMAGE_MAX_WIDTH
        max_height = self.settings.CHAT_IMAGE_MAX_HEIGHT

        # 使用 thumbnail 方法進行等比例縮放
        # 注意: thumbnail 會直接修改原圖,不返回新圖
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        return img

    async def to_graph_format(self, attachment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換為 Graph 格式

        將圖片轉為 Base64 編碼,供 Ollama Vision API 使用。
        """
        # 從磁碟讀取圖片
        file_path = Path(attachment_info["file_path"])

        if not file_path.exists():
            raise FileProcessingError(
                f"圖片檔案不存在: {file_path}",
                details={"attachment_id": attachment_info["id"]},
            )

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        # Base64 編碼
        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        # 從 extra_data 取得圖片資訊
        extra_data = attachment_info.get("extra_data", {})

        # 返回 Graph 需要的格式
        return {
            "id": attachment_info["id"],
            "type": "image",
            "content": base64_data,  # LLM 需要的內容
            "metadata": {
                "width": extra_data.get("width"),
                "height": extra_data.get("height"),
                "mime_type": attachment_info["mime_type"],
                "original_filename": attachment_info["original_filename"],
            },
        }
