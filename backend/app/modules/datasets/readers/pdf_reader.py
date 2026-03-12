# -*- coding: utf-8 -*-
"""
PDF Content Reader

使用 pymupdf4llm 將 PDF 轉換為 Markdown 格式的文字內容
"""
import asyncio

from loguru import logger

from .base import BaseContentReader


class PDFReader(BaseContentReader):
    """
    PDF Reader

    使用 pymupdf4llm 擷取 PDF 文字內容，輸出為 Markdown 格式，
    對標題、表格等結構保留效果最佳，特別適合 RAG 場景。
    """

    async def read(self, file_path: str) -> str:
        """
        從 PDF 擷取文字內容

        Args:
            file_path: PDF 檔案的絕對路徑

        Returns:
            str: Markdown 格式的文字內容

        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: PDF 無法解析或內容為空
            RuntimeError: pymupdf4llm 未安裝
        """
        try:
            import pymupdf4llm
        except ImportError:
            raise RuntimeError(
                "pymupdf4llm 未安裝，請執行: uv pip install pymupdf4llm"
            )

        try:
            content = await asyncio.to_thread(
                pymupdf4llm.to_markdown, file_path
            )
        except FileNotFoundError:
            logger.error(f"[PDFReader] 檔案不存在：{file_path}")
            raise
        except Exception as e:
            logger.error(f"[PDFReader] PDF 解析失敗：{file_path}, {e}")
            raise ValueError(f"PDF 解析失敗：{e}")

        if not content.strip():
            raise ValueError("PDF 檔案無可擷取的文字內容")

        logger.info(
            f"[PDFReader] 成功讀取：{file_path}，長度 {len(content)} 字元"
        )
        return content
