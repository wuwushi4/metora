# -*- coding: utf-8 -*-
"""
純文字 Content Reader

處理 .txt、.md、.json 等可直接以 UTF-8 讀取的檔案
"""
import asyncio

from loguru import logger

from .base import BaseContentReader


class PlainTextReader(BaseContentReader):
    """
    純文字 Reader

    以 UTF-8 編碼讀取檔案內容，適用於 .txt、.md、.json 等純文字格式。
    """

    async def read(self, file_path: str) -> str:
        """
        以 UTF-8 讀取檔案內容

        Args:
            file_path: 檔案的絕對路徑

        Returns:
            str: 檔案的文字內容

        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: 檔案為空或編碼錯誤
        """
        try:
            content = await asyncio.to_thread(self._read_file, file_path)
        except FileNotFoundError:
            logger.error(f"[PlainTextReader] 檔案不存在：{file_path}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"[PlainTextReader] 編碼錯誤：{file_path}, {e}")
            raise ValueError(f"檔案編碼錯誤，請確認檔案為 UTF-8 編碼：{e}")

        if not content.strip():
            raise ValueError("檔案內容為空")

        logger.info(f"[PlainTextReader] 成功讀取：{file_path}，長度 {len(content)} 字元")
        return content

    @staticmethod
    def _read_file(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
