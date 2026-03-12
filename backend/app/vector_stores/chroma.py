# -*- coding: utf-8 -*-
"""
ChromaDB 向量資料庫實作

實作 BaseVectorStore 抽象介面，提供 ChromaDB 後端支援
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Dict, List, Optional

import chromadb
from chromadb import Collection as ChromaCollection
from chromadb import PersistentClient
from loguru import logger

from app.core.config import settings
from app.vector_stores.base import (
    BaseCollection,
    BaseVectorStore,
    GetResult,
    QueryResult,
)


# 用於執行同步 ChromaDB 操作的執行緒池
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="chroma_")


class ChromaCollectionWrapper(BaseCollection):
    """
    ChromaDB Collection 包裝器

    將同步的 ChromaDB Collection 操作包裝為異步介面
    """

    def __init__(self, collection: ChromaCollection):
        self._collection = collection

    @property
    def name(self) -> str:
        return self._collection.name

    async def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """新增向量到集合（異步包裝）"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            _executor,
            partial(
                self._collection.add,
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            ),
        )

    async def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> QueryResult:
        """向量相似度查詢（異步包裝）"""
        if include is None:
            include = ["documents", "metadatas", "distances"]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            partial(
                self._collection.query,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                include=include,
            ),
        )

        return QueryResult(
            ids=result["ids"],
            documents=result.get("documents"),
            metadatas=result.get("metadatas"),
            distances=result.get("distances"),
            embeddings=result.get("embeddings"),
        )

    async def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None,
    ) -> GetResult:
        """直接獲取文檔（異步包裝）"""
        if include is None:
            include = ["documents", "metadatas"]

        loop = asyncio.get_event_loop()

        # 構建參數
        kwargs: Dict[str, Any] = {"include": include}
        if ids is not None:
            kwargs["ids"] = ids
        if where is not None:
            kwargs["where"] = where

        result = await loop.run_in_executor(
            _executor,
            partial(self._collection.get, **kwargs),
        )

        return GetResult(
            ids=result["ids"],
            documents=result.get("documents"),
            metadatas=result.get("metadatas"),
            embeddings=result.get("embeddings"),
        )

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> None:
        """刪除文檔（異步包裝）"""
        loop = asyncio.get_event_loop()

        kwargs: Dict[str, Any] = {}
        if ids is not None:
            kwargs["ids"] = ids
        if where is not None:
            kwargs["where"] = where

        await loop.run_in_executor(
            _executor,
            partial(self._collection.delete, **kwargs),
        )

    async def count(self) -> int:
        """取得文檔數量（異步包裝）"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self._collection.count,
        )


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB 向量資料庫實作

    使用 PersistentClient 進行本地持久化存儲
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """
        初始化 ChromaDB 向量資料庫

        Args:
            persist_directory: 持久化目錄路徑，預設使用 settings.VECTOR_STORE_DIR
        """
        self._persist_directory = persist_directory or settings.VECTOR_STORE_DIR
        self._client: Optional[PersistentClient] = None

    @property
    def client(self) -> PersistentClient:
        """取得 ChromaDB 客戶端"""
        if self._client is None:
            raise RuntimeError("ChromaDB 尚未初始化，請先調用 initialize()")
        return self._client

    async def initialize(self) -> None:
        """初始化 ChromaDB 客戶端"""
        if self._client is not None:
            logger.warning("ChromaDB 客戶端已存在，返回現有實例")
            return

        logger.info("正在初始化 ChromaDB 客戶端...")
        logger.info(f"  - 持久化目錄: {self._persist_directory}")

        loop = asyncio.get_event_loop()

        try:
            # 嘗試使用持久化模式
            try:
                self._client = await loop.run_in_executor(
                    _executor,
                    partial(
                        chromadb.PersistentClient,
                        path=self._persist_directory,
                    ),
                )
            except Exception as persist_error:
                logger.warning(f"持久化模式初始化失敗: {persist_error}")
                logger.warning("改用記憶體模式 (僅用於開發測試)")
                self._client = await loop.run_in_executor(
                    _executor,
                    chromadb.EphemeralClient,
                )

            # 測試連線
            await loop.run_in_executor(_executor, self._client.heartbeat)

            logger.info("✅ ChromaDB 客戶端已初始化")

        except Exception as e:
            logger.error(f"❌ ChromaDB 客戶端初始化失敗: {e}")
            raise

    async def close(self) -> None:
        """關閉 ChromaDB 客戶端"""
        # ChromaDB PersistentClient 由 Python GC 自動回收
        self._client = None
        logger.info("ChromaDB 客戶端已關閉")

    async def heartbeat(self) -> bool:
        """檢查連線狀態"""
        if self._client is None:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(_executor, self._client.heartbeat)
            return True
        except Exception:
            return False

    async def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BaseCollection:
        """取得或建立集合"""
        loop = asyncio.get_event_loop()

        collection = await loop.run_in_executor(
            _executor,
            partial(
                self.client.get_or_create_collection,
                name=name,
                metadata=metadata or {},
            ),
        )

        return ChromaCollectionWrapper(collection)

    async def get_collection(self, name: str) -> BaseCollection:
        """取得現有集合"""
        loop = asyncio.get_event_loop()

        try:
            collection = await loop.run_in_executor(
                _executor,
                partial(self.client.get_collection, name=name),
            )
            return ChromaCollectionWrapper(collection)
        except Exception as e:
            raise ValueError(f"集合 '{name}' 不存在: {e}")

    async def delete_collection(self, name: str) -> None:
        """刪除集合"""
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            _executor,
            partial(self.client.delete_collection, name=name),
        )

        logger.info(f"已刪除集合: {name}")

    async def list_collections(self) -> List[str]:
        """列出所有集合名稱"""
        loop = asyncio.get_event_loop()

        collections = await loop.run_in_executor(
            _executor,
            self.client.list_collections,
        )

        return [col.name for col in collections]


# ==========================================
# 向下相容的全局函式（逐步棄用）
# ==========================================

_chroma_store: Optional[ChromaVectorStore] = None


def get_chroma_store() -> ChromaVectorStore:
    """
    取得 ChromaDB 向量資料庫實例（單例）

    Returns:
        ChromaVectorStore 實例
    """
    global _chroma_store
    if _chroma_store is None:
        _chroma_store = ChromaVectorStore()
    return _chroma_store


async def init_chroma() -> ChromaVectorStore:
    """
    初始化 ChromaDB（向下相容）

    Returns:
        ChromaVectorStore 實例
    """
    store = get_chroma_store()
    await store.initialize()
    return store


def get_chroma_client() -> PersistentClient:
    """
    取得 ChromaDB 客戶端（向下相容）

    ⚠️ 此函式將逐步棄用，請改用 get_chroma_store()

    Returns:
        ChromaDB PersistentClient 實例
    """
    store = get_chroma_store()
    return store.client
