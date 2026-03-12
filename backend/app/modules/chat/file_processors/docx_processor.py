# -*- coding: utf-8 -*-
"""
Word 文件處理器 - 支援 .docx 檔案

這些檔案透過 Sandbox 容器讓 LLM 生成 Python 程式碼（使用 python-docx）來讀取和修改。
"""

import os
from loguru import logger
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import UploadFile

from .base import BaseFileProcessor
from .exceptions import FileValidationError, FileSizeExceededError


# 支援的 Word 文件 MIME 類型
DOCX_MIME_TYPES = {
    # .docx (Office Open XML)
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# 允許的副檔名（不支援舊版 .doc，因為 python-docx 不支援）
DOCX_EXTENSIONS = {".docx"}

# Magic bytes: .docx 是 ZIP 格式 (Office Open XML)
DOCX_MAGIC = b"PK"


class DocxProcessor(BaseFileProcessor):
    """
    Word 文件處理器

    功能:
    - 驗證檔案格式和大小
    - 儲存原始檔案到磁碟（不做轉換）
    - 提供 file 類型的 graph format，供 Agent Graph 注入到 Sandbox
    """

    # 最大檔案大小: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024

    async def validate(self, file: UploadFile) -> None:
        """
        驗證 Word 文件

        檢查項目:
        1. 檔案大小
        2. 副檔名
        3. Magic Number
        """
        # 1. 檔案大小驗證
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > self.MAX_FILE_SIZE:
            raise FileSizeExceededError(file_size, self.MAX_FILE_SIZE, file.filename)

        # 2. 副檔名驗證
        ext = Path(file.filename).suffix.lower()
        if ext not in DOCX_EXTENSIONS:
            raise FileValidationError(
                f"不支援的 Word 文件格式: {ext}",
                details={
                    "filename": file.filename,
                    "supported": list(DOCX_EXTENSIONS),
                },
            )

        # 3. Magic Number 驗證 (.docx 是 ZIP 格式，以 PK 開頭)
        header = await file.read(2)
        file.file.seek(0)

        if not header.startswith(DOCX_MAGIC):
            raise FileValidationError(
                "不是有效的 Word 文件 (.docx)",
                details={"filename": file.filename},
            )

    async def process(self, file: UploadFile, save_dir: Path) -> Dict[str, Any]:
        """
        處理 Word 文件：驗證並儲存原始檔案

        不做任何轉換，直接儲存原始檔案供後續 Sandbox 使用。
        """
        # 1. 驗證
        await self.validate(file)

        # 2. 讀取檔案內容
        content = await file.read()
        file.file.seek(0)

        # 3. 生成安全檔名並儲存
        filename = self._generate_safe_filename(file.filename)
        save_path = self._get_storage_path(filename, save_dir)

        with open(save_path, "wb") as f:
            f.write(content)

        file_size = save_path.stat().st_size

        logger.info(
            f"Word 文件處理完成: {file.filename} -> {filename}",
            extra={
                "file_size": file_size,
                "extension": Path(file.filename).suffix.lower(),
            },
        )

        # 4. 返回附件資訊
        attachment_id = str(uuid4())
        return {
            "id": attachment_id,
            "type": "file",
            "file_path": str(save_path),
            "original_filename": file.filename,
            "file_size": file_size,
            "mime_type": file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "extra_data": {
                "extension": Path(file.filename).suffix.lower(),
            },
        }

    async def to_graph_format(self, attachment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換為 Graph 格式

        Word 文件不轉為 Base64 嵌入 LLM 訊息，而是回傳 file 類型，
        讓 Agent Graph 將檔案注入 Sandbox 容器。
        """
        return {
            "id": attachment_info["id"],
            "type": "file",
            "file_path": attachment_info["file_path"],
            "original_filename": attachment_info["original_filename"],
            "metadata": {
                "file_size": attachment_info["file_size"],
                "mime_type": attachment_info["mime_type"],
                "extension": attachment_info.get("extra_data", {}).get("extension", ""),
            },
        }
