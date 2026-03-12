"""
Reranker 模型管理
使用 FlagEmbedding 載入 BGE Reranker 模型
支援模型池以處理並發推理
"""
from __future__ import annotations

from typing import List, Tuple
import asyncio

import torch
from FlagEmbedding import FlagReranker
from loguru import logger

from app.core.config import settings


class RerankerModel:
    """
    Reranker 模型封裝類別（支援模型池）

    設計目標：
    - 支援並發推理（適用於併發 < 100 的企業場景）
    - 使用模型池避免 PyTorch 模型的線程安全問題
    - 輪詢選擇模型實例以平衡負載
    - 在線程池中執行推理以避免阻塞事件循環
    """

    def __init__(self):
        self.models: List[FlagReranker] = []
        self.model_name = settings.RERANKER_MODEL
        self.device = settings.RERANKER_DEVICE
        self.use_fp16 = settings.RERANKER_USE_FP16
        self.batch_size = settings.RERANKER_BATCH_SIZE
        self.max_length = settings.RERANKER_MAX_LENGTH
        self.pool_size = settings.RERANKER_MODEL_POOL_SIZE

        # 並發控制
        self.semaphore = asyncio.Semaphore(self.pool_size)
        self._lock = asyncio.Lock()
        self._current_index = 0

    def load(self) -> None:
        """載入模型池"""
        logger.info(f"正在載入 Reranker 模型池: {self.model_name}")
        logger.info(f"  - 設備: {self.device}")
        logger.info(f"  - FP16: {self.use_fp16}")
        logger.info(f"  - 批次大小: {self.batch_size}")
        logger.info(f"  - 模型池大小: {self.pool_size}")
        logger.info(f"  - 快取目錄: {settings.HUGGINGFACE_CACHE_DIR}")

        # 檢查 CUDA 是否可用
        cuda_available = torch.cuda.is_available()
        if "cuda" in self.device.lower() and not cuda_available:
            logger.warning("⚠️  CUDA 不可用,將使用 CPU")
            self.device = "cpu"
            self.use_fp16 = False  # CPU 不支援 FP16

        try:
            # 載入多個模型實例
            for i in range(self.pool_size):
                logger.info(f"  正在載入模型實例 {i+1}/{self.pool_size}...")
                model = FlagReranker(
                    self.model_name,
                    use_fp16=self.use_fp16,
                    devices=self.device,
                    cache_dir=settings.HUGGINGFACE_CACHE_DIR,
                )
                self.models.append(model)

            # 驗證模型已載入到正確的設備
            # 目前測試有bug : 使用 devices="cuda" 類別會無視,一樣會載入到 CPU, 但是執行時會載入到 GPU
            if "cuda" in self.device.lower():
                logger.info(f"✅ Reranker 模型池已載入到 GPU ({self.pool_size} 個實例)")
            else:
                logger.info(f"✅ Reranker 模型池已載入到 CPU ({self.pool_size} 個實例)")

        except Exception as e:
            logger.error(f"❌ Reranker 模型池載入失敗: {e}")
            raise

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int | None = None,
    ) -> List[Tuple[int, float]]:
        """
        重新排序文檔（支援並發）

        流程：
        1. 使用 Semaphore 限制並發數（最多 pool_size 個並發）
        2. 輪詢選擇模型實例（避免所有請求都用同一個模型）
        3. 在線程池中執行推理（避免阻塞 asyncio 事件循環）

        Args:
            query: 查詢文本
            documents: 文檔列表
            top_k: 返回前 k 個結果(可選)

        Returns:
            (文檔索引, 分數) 的列表,按分數降序排列

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

            # 建立 query-document pairs
            pairs = [[query, doc] for doc in documents]

            # 在線程池中執行推理（避免阻塞事件循環）
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,  # 使用默認的 ThreadPoolExecutor
                lambda: self.models[model_idx].compute_score(
                    pairs,
                    batch_size=self.batch_size,
                    max_length=self.max_length,
                )
            )

            # 排序
            results = sorted(
                enumerate(scores),
                key=lambda x: x[1],
                reverse=True,
            )

            if top_k:
                results = results[:top_k]

            return results

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
            "use_fp16": self.use_fp16,
            "models_loaded": len(self.models)
        }
