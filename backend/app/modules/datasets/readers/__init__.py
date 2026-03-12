# -*- coding: utf-8 -*-
"""
Content Reader 模組

提供多種檔案類型的文字內容擷取統一介面
"""
from .base import BaseContentReader
from .plain_text_reader import PlainTextReader
from .pdf_reader import PDFReader
from .reader_factory import ReaderFactory

__all__ = [
    "BaseContentReader",
    "PlainTextReader",
    "PDFReader",
    "ReaderFactory",
]
