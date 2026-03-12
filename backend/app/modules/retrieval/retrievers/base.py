# -*- coding: utf-8 -*-
"""
檢索器基礎抽象類別
定義所有檢索器的統一介面
"""
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

# TYPE_CHECKING：僅在類型檢查時導入，避免運行時循環引用
if TYPE_CHECKING:
    from app.modules.retrieval.schemas import Document


class BaseRetriever(ABC):
    """
    檢索器基礎類別

    所有檢索器必須實作此介面，確保檢索方法的一致性。
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        collection_id: int,
        top_k: int = 10
    ) -> List["Document"]:
        """
        執行檢索

        Args:
            query: 查詢文本
            collection_id: Collection ID
            top_k: 返回結果數量

        Returns:
            檢索結果列表（Document 物件）

        Raises:
            可能拋出特定檢索器的異常
        """
        pass
