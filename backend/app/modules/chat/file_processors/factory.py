"""
檔案處理器工廠類別
"""

from loguru import logger
from pathlib import Path
from typing import Dict, Type

from .base import BaseFileProcessor
from .exceptions import UnsupportedFileTypeError
from .image_processor import ImageProcessor
from .pdf_processor import PDFProcessor
from .spreadsheet_processor import SpreadsheetProcessor
from .docx_processor import DocxProcessor




class ProcessorFactory:
    """
    檔案處理器工廠

    使用工廠模式根據檔案類型返回對應的處理器實例。
    """

    # 類別級別的處理器註冊表
    _processors: Dict[str, Type[BaseFileProcessor]] = {}

    @classmethod
    def register(
        cls, extensions: list[str], processor_class: Type[BaseFileProcessor]
    ):
        """
        註冊處理器

        Args:
            extensions: 支援的副檔名列表 (如 ['.jpg', '.png'])
            processor_class: 處理器類別
        """
        for ext in extensions:
            ext_lower = ext.lower()
            if not ext_lower.startswith("."):
                ext_lower = f".{ext_lower}"
            cls._processors[ext_lower] = processor_class
            logger.debug(f"註冊處理器: {ext_lower} -> {processor_class.__name__}")

    @classmethod
    def get_processor(cls, filename: str, settings) -> BaseFileProcessor:
        """
        根據檔名取得處理器實例

        Args:
            filename: 檔案名稱
            settings: 應用配置物件

        Returns:
            對應的處理器實例

        Raises:
            UnsupportedFileTypeError: 不支援的檔案類型
        """
        ext = cls._get_file_extension(filename)
        processor_class = cls._processors.get(ext)

        if not processor_class:
            raise UnsupportedFileTypeError(
                file_type=ext, supported_types=list(cls._processors.keys())
            )

        return processor_class(settings)

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """取得所有支援的副檔名"""
        return list(cls._processors.keys())

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """
        提取檔案副檔名

        Args:
            filename: 檔案名稱

        Returns:
            小寫的副檔名 (含點號,如 ".jpg")
        """
        ext = Path(filename).suffix.lower()
        if not ext:
            raise UnsupportedFileTypeError(
                file_type="無副檔名", supported_types=["有效的檔案副檔名"]
            )
        return ext


# 預先註冊處理器
ProcessorFactory.register(
    [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"], ImageProcessor
)

# PDF 處理器註冊 (待實作完成後啟用)
ProcessorFactory.register([".pdf"], PDFProcessor)

# 試算表處理器註冊
ProcessorFactory.register([".xlsx", ".xls", ".csv"], SpreadsheetProcessor)

# Word 文件處理器註冊
ProcessorFactory.register([".docx"], DocxProcessor)

logger.info(f"已註冊處理器: {ProcessorFactory.get_supported_extensions()}")
