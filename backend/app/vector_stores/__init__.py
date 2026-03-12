# -*- coding: utf-8 -*-
"""
向量存儲模組

提供統一的向量資料庫抽象介面，支援多種後端實作：
- ChromaDB: 輕量級本地向量資料庫
- PGVector: PostgreSQL + pgvector 擴展

使用方式:
    from app.vector_stores.factory import create_vector_store
    
    # 根據環境變數 VECTOR_STORE_PROVIDER 自動選擇後端
    vector_store = create_vector_store()
    await vector_store.initialize()
    
    # 使用統一介面操作
    collection = await vector_store.get_or_create_collection("my_collection")
    await collection.add(ids, embeddings, documents, metadatas)
    results = await collection.query(query_embeddings, n_results=10)
"""
from app.vector_stores.base import (
    BaseCollection,
    BaseVectorStore,
    GetResult,
    QueryResult,
)
from app.vector_stores.factory import VectorStoreFactory, create_vector_store

__all__ = [
    # 抽象介面
    "BaseVectorStore",
    "BaseCollection",
    "QueryResult",
    "GetResult",
    # 工廠
    "VectorStoreFactory",
    "create_vector_store",
]

