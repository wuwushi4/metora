# -*- coding: utf-8 -*-
"""
向量資料庫工廠模組

提供統一的向量資料庫實例建立介面，根據配置選擇不同的後端實作
"""
from __future__ import annotations

from typing import Optional

from loguru import logger

from app.core.config import settings
from app.vector_stores.base import BaseVectorStore


class VectorStoreFactory:
    """
    向量資料庫工廠

    根據環境變數 VECTOR_STORE_PROVIDER 建立對應的向量資料庫實例
    """

    @staticmethod
    def create(provider: Optional[str] = None) -> BaseVectorStore:
        """
        建立向量資料庫實例

        Args:
            provider: 向量資料庫提供者，可選值:
                - "chroma": ChromaDB（預設）
                - "pgvector": PostgreSQL + pgvector

        Returns:
            BaseVectorStore 實例

        Raises:
            ValueError: 不支援的提供者
        """
        # 使用傳入的 provider 或從設定讀取
        provider = provider or getattr(settings, "VECTOR_STORE_PROVIDER", "chroma")
        provider = provider.lower()

        logger.info(f"建立向量資料庫實例: provider={provider}")

        if provider == "chroma":
            from app.vector_stores.chroma import ChromaVectorStore

            return ChromaVectorStore(
                persist_directory=settings.VECTOR_STORE_DIR,
            )

        elif provider == "pgvector":
            from app.vector_stores.pgvector import PGVectorStore

            return PGVectorStore(
                database_url=settings.DATABASE_URL,
                table_prefix=getattr(settings, "PGVECTOR_TABLE_PREFIX", "vector_"),
                embedding_dim=getattr(settings, "PGVECTOR_EMBEDDING_DIM", 1024),
                distance_metric=settings.VECTOR_DISTANCE_METRIC,
            )

        else:
            raise ValueError(
                f"不支援的向量資料庫提供者: {provider}。"
                f"支援的選項: chroma, pgvector"
            )


def create_vector_store(provider: Optional[str] = None) -> BaseVectorStore:
    """
    建立向量資料庫實例（便捷函式）

    Args:
        provider: 向量資料庫提供者

    Returns:
        BaseVectorStore 實例
    """
    return VectorStoreFactory.create(provider)

