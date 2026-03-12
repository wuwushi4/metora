"""
全局資源管理器
統一管理所有系統資源的生命週期
"""
from __future__ import annotations

import redis.asyncio as redis
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.core.database import close_database, init_database
from app.core.redis import close_redis, init_redis
from app.models.embeddings import EmbeddingModel
from app.models.model_loader import load_embedding_model, load_reranker_model
from app.models.reranker import RerankerModel
from app.vector_stores.base import BaseVectorStore
from app.vector_stores.factory import create_vector_store
from app.modules.retrieval.retrievers.vector import VectorRetriever
from app.modules.retrieval.retrievers.bm25 import BM25Retriever
from app.modules.retrieval.retrievers.hybrid import HybridRetriever
from app.llm.factory import LLMProviderFactory
from app.llm.base import BaseLLMProvider


class ResourceManager:
    """
    全局資源管理器
    負責初始化、持有、清理所有系統資源
    """

    def __init__(self):
        # 資料庫與快取
        self.db_engine: AsyncEngine | None = None
        self.redis_client: redis.Redis | None = None

        # AI 模型
        self.embedding_model: EmbeddingModel | None = None
        self.reranker_model: RerankerModel | None = None

        # 向量資料庫（抽象介面）
        self.vector_store: BaseVectorStore | None = None

        # 檢索器（新架構）
        self.vector_retriever: VectorRetriever | None = None
        self.bm25_retriever: BM25Retriever | None = None
        self.hybrid_retriever: HybridRetriever | None = None

        # LLM Provider 和 Graph Registry
        self.llm_provider: BaseLLMProvider | None = None

    async def initialize(self) -> None:
        """
        初始化所有系統資源
        在應用啟動時調用
        """
        logger.info("=" * 60)
        logger.info("🚀 開始初始化系統資源...")
        logger.info("=" * 60)

        try:
            # === 1. 資料庫連線池 ===
            logger.info("[1/9] 初始化資料庫連線池")
            self.db_engine = await init_database()

            # === 2. Redis 連線池 ===
            logger.info("[2/9] 初始化 Redis 連線池")
            self.redis_client = await init_redis()

            # === 3. Embedding 模型池 ===
            logger.info("[3/9] 載入 Embedding 模型池")
            self.embedding_model = load_embedding_model()

            # === 4. Reranker 模型池（條件載入）===
            logger.info("[4/9] 載入 Reranker 模型池")
            if settings.RERANKER_ENABLED:
                self.reranker_model = load_reranker_model()
            else:
                logger.info("⏭️  Reranker 已停用，跳過載入")

            # === 5. 向量資料庫 ===
            logger.info(f"[5/9] 初始化向量資料庫 (provider: {settings.VECTOR_STORE_PROVIDER})")
            self.vector_store = create_vector_store()
            await self.vector_store.initialize()

            # === 6. 檢索器架構（新）===
            logger.info("[6/9] 初始化檢索器架構")

            # VectorRetriever
            self.vector_retriever = VectorRetriever(
                vector_store=self.vector_store,
                embedding_model=self.embedding_model
            )
            logger.info("  ✅ VectorRetriever 已就緒")

            # BM25Retriever
            self.bm25_retriever = BM25Retriever(
                vector_store=self.vector_store,
                max_cache_size=50  # 可配置
            )
            logger.info("  ✅ BM25Retriever 已就緒 (索引將在使用時動態建立)")

            # HybridRetriever
            self.hybrid_retriever = HybridRetriever(
                vector_retriever=self.vector_retriever,
                bm25_retriever=self.bm25_retriever,
                reranker_model=self.reranker_model
            )
            logger.info("  ✅ HybridRetriever 已就緒")

            # === 7. LLM Provider ===
            logger.info("[7/9] 初始化 LLM Provider")
            self.llm_provider = LLMProviderFactory.create_from_settings(settings)
            logger.info("  ✅ LLM Provider 已就緒")

            # === 8. Graph Registry ===
            logger.info("[8/9] 初始化 Graph Registry")
            from app.modules.graphs.registry import initialize_graphs
            from app.modules.retrieval.service import RetrievalService

            # 建立 RetrievalService 實例（用於 rag_graph）
            retrieval_service = RetrievalService(
                hybrid_retriever=self.hybrid_retriever
            )

            # 初始化並註冊所有 Graph
            initialize_graphs(settings, self.llm_provider, retrieval_service)

            # 動態計算已註冊的 Graph 數量
            from app.modules.graphs.registry import GraphRegistry
            graph_count = len(GraphRegistry.list_available())
            logger.info(f"  ✅ Graph Registry 已初始化，已註冊 {graph_count} 個 Graph")

            # === 9. 驗證所有資源 ===
            logger.info("[9/9] 驗證系統資源")
            assert self.db_engine is not None, "資料庫引擎初始化失敗"
            assert self.redis_client is not None, "Redis 初始化失敗"
            assert self.embedding_model is not None, "Embedding 模型載入失敗"
            assert self.vector_store is not None, "向量資料庫初始化失敗"
            assert self.vector_retriever is not None, "VectorRetriever 初始化失敗"
            assert self.bm25_retriever is not None, "BM25Retriever 初始化失敗"
            assert self.hybrid_retriever is not None, "HybridRetriever 初始化失敗"
            assert self.llm_provider is not None, "LLM Provider 初始化失敗"

            logger.info("=" * 60)
            logger.info("✅ 系統資源初始化完成!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 系統資源初始化失敗: {e}")
            # 清理已初始化的資源
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """
        清理所有系統資源
        在應用關閉時調用
        """
        logger.info("=" * 60)
        logger.info("🛑 開始清理系統資源...")
        logger.info("=" * 60)

        # 清理 Graph Registry
        from app.modules.graphs.registry import GraphRegistry
        GraphRegistry.clear()
        logger.info("  ✅ Graph Registry 已清理")

        self.llm_provider = None

        # 清理檢索器
        if self.bm25_retriever:
            await self.bm25_retriever.clear_cache()
            logger.info("  ✅ BM25Retriever 快取已清理")

        self.hybrid_retriever = None
        self.vector_retriever = None
        self.bm25_retriever = None

        # 關閉向量資料庫連線
        if self.vector_store:
            await self.vector_store.close()
            self.vector_store = None
            logger.info("  ✅ 向量資料庫已關閉")

        # 關閉 Redis 連線池
        if self.redis_client:
            await close_redis()
            self.redis_client = None

        # 關閉資料庫連線池
        if self.db_engine:
            await close_database()
            self.db_engine = None

        # AI 模型池由 Python GC 自動回收
        self.embedding_model = None
        self.reranker_model = None

        logger.info("=" * 60)
        logger.info("✅ 系統資源清理完成!")
        logger.info("=" * 60)


# ==========================================
# 全局單例
# ==========================================
_resource_manager: ResourceManager | None = None


def get_resource_manager() -> ResourceManager:
    """
    取得資源管理器單例

    Returns:
        ResourceManager 實例
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
