# -*- coding: utf-8 -*-
"""
遞迴文字分塊器

使用 LangChain 的 RecursiveCharacterTextSplitter 對純文字內容進行分塊，
適用於 PDF、TXT、Markdown 等非結構化文字檔案。
"""
from typing import List, Dict, Any, Optional

from loguru import logger

from .base import BaseChunker
from app.core.config import settings


class RecursiveTextChunker(BaseChunker):
    """
    遞迴文字分塊策略

    使用 RecursiveCharacterTextSplitter 按分隔符遞迴分割文字，
    優先按段落、換行、句號等自然邊界切分，確保分塊內容語義完整。

    適用檔案類型：.pdf、.txt、.md

    參數優先級：建構子傳入值 > 系統設定 (SettingsManager) > 環境變數 (config.settings)
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        **kwargs,
    ):
        from app.modules.settings.manager import settings_manager

        self.chunk_size = (
            chunk_size
            or settings_manager.get("RECURSIVE_TEXT_CHUNK_SIZE")
            or settings.RECURSIVE_TEXT_CHUNK_SIZE
        )
        self.chunk_overlap = (
            chunk_overlap
            or settings_manager.get("RECURSIVE_TEXT_CHUNK_OVERLAP")
            or settings.RECURSIVE_TEXT_CHUNK_OVERLAP
        )

    async def chunk(self, content: str) -> List[Dict[str, Any]]:
        """
        將文字內容遞迴分塊

        Args:
            content: 純文字或 Markdown 格式的文字內容

        Returns:
            List[Dict]: 分塊結果列表

        Raises:
            ValueError: 當內容為空時
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        if not content.strip():
            raise ValueError("文字內容為空，無法進行分塊")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""],
            length_function=len,
        )

        documents = splitter.create_documents([content])

        chunks = []
        for idx, doc in enumerate(documents):
            chunk_text = doc.page_content

            start_pos = content.find(chunk_text)
            end_pos = start_pos + len(chunk_text) if start_pos >= 0 else -1

            chunks.append({
                "content": chunk_text,
                "type": "text_chunk",
                "metadata": {
                    "chunk_index": idx,
                    "representation": "full",
                    "char_start": start_pos if start_pos >= 0 else None,
                    "char_end": end_pos if end_pos >= 0 else None,
                    "chunk_size": len(chunk_text),
                },
            })

        logger.info(
            f"[RecursiveTextChunker] 分塊完成，"
            f"原文 {len(content)} 字元 → {len(chunks)} 個分塊 "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )

        return chunks

    def validate(self, content: str) -> bool:
        """
        驗證內容是否為有效的文字

        Args:
            content: 待驗證的內容

        Returns:
            bool: True 表示內容有效
        """
        if not content or not content.strip():
            return False

        if len(content.strip()) < 10:
            logger.debug("[RecursiveTextChunker] 內容過短（< 10 字元）")
            return False

        return True

    def supported_file_types(self) -> List[str]:
        """遞迴文字策略支援 PDF、TXT、Markdown"""
        return [".pdf", ".txt", ".md"]

    def get_strategy_name(self) -> str:
        """返回策略名稱"""
        return "recursive_text"
