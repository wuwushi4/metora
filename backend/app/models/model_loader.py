"""
模型載入器統一介面
"""
from __future__ import annotations

from loguru import logger

from app.core.config import settings
from app.models.embeddings import EmbeddingModel
from app.models.reranker import RerankerModel


def load_embedding_model() -> EmbeddingModel:
    """
    載入 Embedding 模型

    Returns:
        已載入的 EmbeddingModel 實例
    """
    model = EmbeddingModel()
    model.load()
    return model


def load_reranker_model() -> RerankerModel | None:
    """
    條件載入 Reranker 模型
    只有當 RERANKER_ENABLED=True 時才載入

    Returns:
        已載入的 RerankerModel 實例,或 None
    """
    if not settings.RERANKER_ENABLED:
        logger.info("⏭️  Reranker 已停用,跳過載入")
        return None

    model = RerankerModel()
    model.load()
    return model
