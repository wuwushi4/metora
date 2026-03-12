# -*- coding: utf-8 -*-
"""
分塊策略基礎抽象類別
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseChunker(ABC):
    """
    分塊策略抽象基類

    所有分塊策略都應該繼承此類並實作 chunk() 和 validate() 方法
    """

    @abstractmethod
    async def chunk(self, content: str) -> List[Dict[str, Any]]:
        """
        將內容分塊

        Args:
            content: 原始文件內容

        Returns:
            List[Dict]: 分塊結果列表，每個分塊包含：
                {
                    "content": "分塊內容（用於向量化）",
                    "type": "chunk_type（如：qa_full, question_only）",
                    "metadata": {
                        "chunk_index": 分塊索引,
                        "representation": "表徵類型",
                        ...其他元數據
                    }
                }

        Raises:
            ValueError: 當內容格式不符合策略要求時
        """
        pass

    @abstractmethod
    def validate(self, content: str) -> bool:
        """
        驗證內容格式是否符合此策略

        Args:
            content: 原始文件內容

        Returns:
            bool: True 表示內容格式符合，False 表示不符合
        """
        pass

    def get_strategy_name(self) -> str:
        """
        獲取策略名稱（預設返回類別名稱）

        Returns:
            str: 策略名稱
        """
        return self.__class__.__name__

    def supported_file_types(self) -> List[str]:
        """
        回傳此策略支援的檔案副檔名列表（含點號）

        子類別應覆寫此方法以宣告自己支援的檔案類型。
        預設回傳空列表表示不限制。

        Returns:
            List[str]: 支援的副檔名列表，如 [".json", ".pdf"]
        """
        return []
