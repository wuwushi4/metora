# -*- coding: utf-8 -*-
"""
向量存儲抽象介面

定義統一的向量資料庫操作介面，支援多種後端實作（ChromaDB, PGVector 等）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QueryResult:
    """
    向量查詢結果

    統一的查詢結果格式，與具體向量資料庫實作無關
    """
    ids: List[List[str]]
    documents: Optional[List[List[str]]] = None
    metadatas: Optional[List[List[Dict[str, Any]]]] = None
    distances: Optional[List[List[float]]] = None
    embeddings: Optional[List[List[List[float]]]] = None


@dataclass
class GetResult:
    """
    直接獲取結果（非向量查詢）

    用於 metadata 過濾查詢
    """
    ids: List[str]
    documents: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None
    embeddings: Optional[List[List[float]]] = None


class BaseCollection(ABC):
    """
    Collection 抽象介面

    定義向量集合的標準操作
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """取得 Collection 名稱"""
        ...

    @abstractmethod
    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        新增向量到集合

        Args:
            ids: 文檔 ID 列表
            embeddings: 向量列表
            documents: 原文列表
            metadatas: metadata 列表
        """
        ...

    @abstractmethod
    async def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> QueryResult:
        """
        向量相似度查詢

        Args:
            query_embeddings: 查詢向量列表
            n_results: 返回結果數量
            where: metadata 過濾條件
            include: 要包含的欄位 ["documents", "metadatas", "distances", "embeddings"]

        Returns:
            QueryResult 查詢結果
        """
        ...

    @abstractmethod
    async def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> GetResult:
        """
        直接獲取文檔（非向量查詢）

        Args:
            ids: 要獲取的文檔 ID 列表
            where: metadata 過濾條件
            include: 要包含的欄位 ["documents", "metadatas", "embeddings"]

        Returns:
            GetResult 獲取結果
        """
        ...

    @abstractmethod
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        刪除文檔

        Args:
            ids: 要刪除的文檔 ID 列表
            where: metadata 過濾條件（二選一）
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """
        取得集合中的文檔數量

        Returns:
            文檔數量
        """
        ...


class BaseVectorStore(ABC):
    """
    向量資料庫抽象介面

    定義向量資料庫的標準操作
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化向量資料庫連線

        在應用啟動時調用
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """
        關閉向量資料庫連線

        在應用關閉時調用
        """
        ...

    @abstractmethod
    async def heartbeat(self) -> bool:
        """
        檢查連線狀態

        Returns:
            True 表示連線正常，False 表示連線異常
        """
        ...

    @abstractmethod
    async def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BaseCollection:
        """
        取得或建立集合

        Args:
            name: 集合名稱
            metadata: 集合元數據

        Returns:
            Collection 實例
        """
        ...

    @abstractmethod
    async def get_collection(self, name: str) -> BaseCollection:
        """
        取得現有集合

        Args:
            name: 集合名稱

        Returns:
            Collection 實例

        Raises:
            ValueError: 集合不存在時
        """
        ...

    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """
        刪除集合

        Args:
            name: 集合名稱
        """
        ...

    @abstractmethod
    async def list_collections(self) -> List[str]:
        """
        列出所有集合名稱

        Returns:
            集合名稱列表
        """
        ...
