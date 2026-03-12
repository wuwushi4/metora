# -*- coding: utf-8 -*-
"""
向量檢索器
基於向量資料庫和 Embedding 模型的語義向量檢索
"""
from typing import List

from loguru import logger

from app.models.embeddings import EmbeddingModel
from app.modules.retrieval.retrievers.base import BaseRetriever
from app.modules.retrieval.schemas import Document
from app.vector_stores.base import BaseVectorStore


class VectorRetriever(BaseRetriever):
    """
    向量檢索器 - 基於抽象向量資料庫介面

    職責：
    1. 查詢向量編碼（使用 EmbeddingModel 模型池）
    2. 向量資料庫向量檢索
    3. 距離轉分數（支援多種距離度量）
    4. 閾值過濾
    5. 結果轉換為 Document 物件

    並發安全：
    - 使用 EmbeddingModel 的模型池處理並發推理
    - 向量資料庫的讀操作是線程安全的
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding_model: EmbeddingModel
    ):
        self.vector_store = vector_store
        self.embedding = embedding_model

    async def search(
        self,
        query: str,
        collection_id: int,
        top_k: int = 10
    ) -> List[Document]:
        """
        執行向量檢索

        Args:
            query: 查詢文本
            collection_id: Collection ID
            top_k: 返回結果數量

        Returns:
            檢索結果列表（Document 物件）
        """
        try:
            from app.core.config import settings

            collection_name = f"collection_{collection_id}"
            vector_collection = await self.vector_store.get_collection(name=collection_name)

            # 查詢向量編碼（使用模型池，支援並發）
            query_embedding = (await self.embedding.encode([query]))[0]

            # 向量資料庫查詢
            results = await vector_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # 轉換為 Document 物件
            documents = []
            for i in range(len(results.ids[0])):
                # 根據距離度量類型轉換分數
                distance = results.distances[0][i] if results.distances else 0.0
                score = self._distance_to_score(distance, settings.VECTOR_DISTANCE_METRIC)

                documents.append(Document(
                    id=results.ids[0][i],
                    content=results.documents[0][i] if results.documents else "",
                    metadata=results.metadatas[0][i] if results.metadatas else {},
                    score=score
                ))

            # 根據閾值過濾低分結果
            if settings.VECTOR_SEARCH_SCORE_THRESHOLD > 0:
                original_count = len(documents)
                documents = [
                    doc for doc in documents
                    if doc.score >= settings.VECTOR_SEARCH_SCORE_THRESHOLD
                ]
                logger.debug(
                    f"向量查詢 : 閾值過濾 ({settings.VECTOR_SEARCH_SCORE_THRESHOLD}): "
                    f"{original_count} → {len(documents)} 個結果"
                )

            logger.debug(
                f"向量檢索完成: collection_{collection_id}, "
                f"返回 {len(documents)} 個結果"
            )

            return documents

        except Exception as e:
            logger.error(f"向量檢索失敗: {e}")
            return []

    def _distance_to_score(self, distance: float, metric: str) -> float:
        """
        將距離轉換為相似度分數

        距離度量說明：
        - cosine: 餘弦距離 [0, 2], score = 1.0 - distance (實際上正規化向量: [0, 1])
        - l2: 平方歐式距離 [0, ∞), score = 1.0 / (1.0 + distance)
        - ip: 內積 [-∞, ∞), score = distance (值越大越相似)

        Args:
            distance: 向量資料庫返回的距離值
            metric: 距離度量類型

        Returns:
            相似度分數（值越大越相似）
        """
        if metric == "cosine":
            # Cosine distance: [0, 2] → score: [1, -1]
            # 對於正規化向量實際範圍: [0, 1] → [1, 0]
            return 1.0 - distance
        elif metric == "l2":
            # Squared L2: [0, ∞) → score: [1, 0]
            return 1.0 / (1.0 + distance)
        elif metric == "ip":
            # Inner product: 值越大越相似，直接使用
            return distance
        else:
            # 未知度量類型，使用 cosine 的轉換方式作為預設
            logger.warning(
                f"未知的距離度量: {metric}, "
                f"使用 cosine 轉換方式"
            )
            return 1.0 - distance
