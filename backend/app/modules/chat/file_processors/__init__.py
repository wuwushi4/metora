"""
檔案處理器模組

提供多種檔案類型的處理器,用於處理聊天附件上傳。
"""

from .base import BaseFileProcessor
from .factory import ProcessorFactory
from .exceptions import (
    FileProcessingError,
    FileValidationError,
    UnsupportedFileTypeError,
    FileSizeExceededError,
)

__all__ = [
    "BaseFileProcessor",
    "ProcessorFactory",
    "FileProcessingError",
    "FileValidationError",
    "UnsupportedFileTypeError",
    "FileSizeExceededError",
]
