# -*- coding: utf-8 -*-
"""
Content Reader 抽象基類
"""
from abc import ABC, abstractmethod


class BaseContentReader(ABC):
    """
    Content Reader 抽象基類

    所有 Reader 都應繼承此類並實作 read() 方法，
    負責將檔案內容轉換為純文字字串供後續分塊使用。
    """

    @abstractmethod
    async def read(self, file_path: str) -> str:
        """
        讀取檔案並回傳文字內容

        Args:
            file_path: 檔案的絕對路徑

        Returns:
            str: 擷取後的純文字內容

        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: 檔案內容無法解析
        """
        pass

    def get_reader_name(self) -> str:
        """回傳 Reader 名稱（預設為類別名稱）"""
        return self.__class__.__name__
