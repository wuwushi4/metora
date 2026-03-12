"""
FastAPI 依賴注入函式
提供便捷的資源注入方式
"""
from __future__ import annotations

import redis.asyncio as redis
from fastapi import Depends

from app.core.database import get_db  # 直接從 database.py 匯入
from app.core.resource_manager import ResourceManager, get_resource_manager
from app.models.embeddings import EmbeddingModel
from app.models.reranker import RerankerModel
from app.vector_stores.base import BaseVectorStore


# ==========================================
# 資源管理器
# ==========================================

def get_resources() -> ResourceManager:
    """
    取得資源管理器

    使用範例:
        @app.get("/example")
        async def example(resources: ResourceManager = Depends(get_resources)):
            embedding = resources.embedding_model
    """
    return get_resource_manager()


# ==========================================
# 資料庫
# ==========================================
# get_db 已從 app.core.database 匯入,直接使用即可


# ==========================================
# Redis
# ==========================================

def get_redis(
    resources: ResourceManager = Depends(get_resources)
) -> redis.Redis:
    """
    取得 Redis 客戶端

    使用範例:
        @app.get("/cache")
        async def get_cache(redis: redis.Redis = Depends(get_redis)):
            value = await redis.get("key")
    """
    if resources.redis_client is None:
        raise RuntimeError("Redis 尚未初始化")
    return resources.redis_client


# ==========================================
# AI 模型
# ==========================================

def get_embedding(
    resources: ResourceManager = Depends(get_resources)
) -> EmbeddingModel:
    """
    取得 Embedding 模型

    使用範例:
        @app.post("/embed")
        async def embed_text(
            embedding: EmbeddingModel = Depends(get_embedding)
        ):
            vectors = await embedding.encode(["hello world"])
    """
    if resources.embedding_model is None:
        raise RuntimeError("Embedding 模型尚未載入")
    return resources.embedding_model


def get_reranker(
    resources: ResourceManager = Depends(get_resources)
) -> RerankerModel:
    """
    取得 Reranker 模型

    使用範例:
        @app.post("/rerank")
        async def rerank_docs(
            reranker: RerankerModel = Depends(get_reranker)
        ):
            results = await reranker.rerank("query", ["doc1", "doc2"])
    """
    if resources.reranker_model is None:
        raise RuntimeError("Reranker 模型尚未載入或已停用")
    return resources.reranker_model


# ==========================================
# 向量資料庫
# ==========================================

def get_vector_store(
    resources: ResourceManager = Depends(get_resources)
) -> BaseVectorStore:
    """
    取得向量資料庫實例

    使用範例:
        @app.get("/collections")
        async def list_collections(
            vector_store: BaseVectorStore = Depends(get_vector_store)
        ):
            return await vector_store.list_collections()
    """
    if resources.vector_store is None:
        raise RuntimeError("向量資料庫尚未初始化")
    return resources.vector_store


# ==========================================
# 檢索服務
# ==========================================

def get_retrieval_service(
    resources: ResourceManager = Depends(get_resources),
):
    """
    取得 RetrievalService - FastAPI 依賴注入

    每次請求創建新實例（無狀態設計）

    使用範例:
        @app.post("/search")
        async def search(
            retrieval_service = Depends(get_retrieval_service)
        ):
            results = await retrieval_service.cross_collection_search(...)
    """
    from app.modules.retrieval.service import RetrievalService

    if resources.hybrid_retriever is None:
        raise RuntimeError("HybridRetriever 尚未初始化")

    return RetrievalService(
        hybrid_retriever=resources.hybrid_retriever
    )
