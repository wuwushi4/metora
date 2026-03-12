# -*- coding: utf-8 -*-
"""
Content Reader 工廠
"""
from typing import Dict, Type

from .base import BaseContentReader
from .plain_text_reader import PlainTextReader
from .pdf_reader import PDFReader


class ReaderFactory:
    """
    Content Reader 工廠

    根據檔案副檔名取得對應的 Reader 實例。
    未來可透過 register() 擴充支援更多檔案類型。
    """

    _readers: Dict[str, Type[BaseContentReader]] = {
        ".json": PlainTextReader,
        ".txt": PlainTextReader,
        ".md": PlainTextReader,
        ".pdf": PDFReader,
    }

    @classmethod
    def get_reader(cls, file_type: str) -> BaseContentReader:
        """
        根據副檔名取得 Reader 實例

        Args:
            file_type: 副檔名（含點號，如 ".pdf"）

        Returns:
            BaseContentReader: Reader 實例

        Raises:
            ValueError: 不支援的檔案類型
        """
        ext = file_type.lower() if file_type.startswith(".") else f".{file_type.lower()}"
        reader_class = cls._readers.get(ext)

        if not reader_class:
            supported = ", ".join(cls._readers.keys())
            raise ValueError(
                f"不支援的檔案類型：{ext}。支援的類型：{supported}"
            )

        return reader_class()

    @classmethod
    def register(cls, extensions: list[str], reader_class: Type[BaseContentReader]) -> None:
        """
        註冊新的 Reader

        Args:
            extensions: 支援的副檔名列表（如 [".docx", ".doc"]）
            reader_class: Reader 類別
        """
        for ext in extensions:
            ext_lower = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            cls._readers[ext_lower] = reader_class

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """取得所有支援的副檔名"""
        return list(cls._readers.keys())
