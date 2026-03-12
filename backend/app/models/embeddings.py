"""
Embedding 模型管理
使用 LangChain HuggingFace Embeddings 載入 BGE 系列模型
支援模型池以處理並發推理
"""
from __future__ import annotations

from typing import List
import asyncio

import torch
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from app.core.config import settings


class EmbeddingModel:
    """
    Embedding 模型封裝類別（支援模型池）

    設計目標：
    - 支援並發推理（適用於併發 < 100 的企業場景）
    - 使用模型池避免 PyTorch 模型的線程安全問題
    - 輪詢選擇模型實例以平衡負載
    - 在線程池中執行推理以避免阻塞事件循環
    """

    def __init__(self):
        self.models: List[HuggingFaceEmbeddings] = []
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.pool_size = settings.EMBEDDING_MODEL_POOL_SIZE

        # 並發控制
        self.semaphore = asyncio.Semaphore(self.pool_size)
        self._lock = asyncio.Lock()
        self._current_index = 0

    def load(self) -> None:
        """載入模型池"""
        logger.info(f"正在載入 Embedding 模型池: {self.model_name}")
        logger.info(f"  - 設備: {self.device}")
        logger.info(f"  - 批次大小: {self.batch_size}")
        logger.info(f"  - 模型池大小: {self.pool_size}")
        logger.info(f"  - 快取目錄: {settings.HUGGINGFACE_CACHE_DIR}")

        # 檢查 CUDA 是否可用
        cuda_available = torch.cuda.is_available()
        if "cuda" in self.device.lower() and not cuda_available:
            logger.warning("⚠️  CUDA 不可用,將使用 CPU")
            self.device = "cpu"

        try:
            # 載入多個模型實例
            for i in range(self.pool_size):
                logger.info(f"  正在載入模型實例 {i+1}/{self.pool_size}...")
                model = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    cache_folder=settings.HUGGINGFACE_CACHE_DIR,
                    model_kwargs={"device": self.device},
                    encode_kwargs={
                        "batch_size": self.batch_size,
                        "normalize_embeddings": True
                    },
                )
                self.models.append(model)

            # 驗證模型已載入到正確的設備
            if "cuda" in self.device.lower():
                logger.info(f"✅ Embedding 模型池已載入到 GPU ({self.pool_size} 個實例)")
            else:
                logger.info(f"✅ Embedding 模型池已載入到 CPU ({self.pool_size} 個實例)")

        except Exception as e:
            logger.error(f"❌ Embedding 模型池載入失敗: {e}")
            raise

    async def encode(
        self,
        texts: List[str],
        batch_size: int | None = None,
    ) -> List[List[float]]:
        """
        將文本編碼為向量（支援並發）

        流程：
        1. 使用 Semaphore 限制並發數（最多 pool_size 個並發）
        2. 輪詢選擇模型實例（避免所有請求都用同一個模型）
        3. 在線程池中執行推理（避免阻塞 asyncio 事件循環）

        Args:
            texts: 待編碼的文本列表
            batch_size: 批次大小(可選,注意:此參數會被忽略,因為 batch_size 在模型初始化時設定)

        Returns:
            向量列表

        Raises:
            RuntimeError: 模型尚未載入
        """
        if not self.models:
            raise RuntimeError("模型尚未載入")

        # 使用 Semaphore 限制並發數
        async with self.semaphore:
            # 輪詢選擇模型實例（線程安全）
            async with self._lock:
                model_idx = self._current_index
                self._current_index = (self._current_index + 1) % len(self.models)

            # 在線程池中執行推理（避免阻塞事件循環）
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,  # 使用默認的 ThreadPoolExecutor
                self.models[model_idx].embed_documents,
                texts
            )

            return embeddings

    def get_pool_stats(self) -> dict:
        """
        獲取模型池統計資訊

        Returns:
            統計資訊字典
        """
        return {
            "pool_size": self.pool_size,
            "model_name": self.model_name,
            "device": self.device,
            "models_loaded": len(self.models)
        }
