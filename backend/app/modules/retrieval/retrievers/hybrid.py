# -*- coding: utf-8 -*-
"""
混合檢索器
整合向量檢索、BM25 檢索、RRF 融合、多表徵去重、BGE 重排序
"""
from typing import List, Dict, Optional
import asyncio
import math
from loguru import logger

from app.core.config import settings
from app.models.reranker import RerankerModel
from app.modules.retrieval.retrievers.base import BaseRetriever
from app.modules.retrieval.retrievers.vector import VectorRetriever
from app.modules.retrieval.retrievers.bm25 import BM25Retriever
from app.modules.retrieval.schemas import Document


class HybridRetriever(BaseRetriever):
    """
    混合檢索器 - 整合多種檢索策略

    職責：
    1. 並行執行向量檢索 + BM25 檢索
    2. RRF (Reciprocal Rank Fusion) 融合
    3. 多重表徵去重（複合鍵：dataset_id + qa_id）
    4. BGE Reranker 重排序（可選）

    設計原則：
    1. 依賴注入：接受 VectorRetriever 和 BM25Retriever
    2. 無狀態：不維護檢索相關的狀態
    3. 並發安全：使用 asyncio.gather() 並行檢索
    4. 單一職責：只負責混合檢索邏輯，不處理具體檢索實作
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        bm25_retriever: BM25Retriever,
        reranker_model: Optional[RerankerModel] = None,
    ):
        """
        初始化混合檢索器

        Args:
            vector_retriever: 向量檢索器
            bm25_retriever: BM25 檢索器
            reranker_model: 重排序模型（可選）
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.reranker = reranker_model

        # 分數正規化配置
        self.reranker_score_normalization = settings.RERANKER_SCORE_NORMALIZATION
        self.rrf_score_normalization = settings.RRF_SCORE_NORMALIZATION
        self.rrf_sigmoid_scale = settings.RRF_SIGMOID_SCALE
        self.rrf_sigmoid_shift = settings.RRF_SIGMOID_SHIFT

    async def search(
        self,
        query: str,
        collection_id: int,
        top_k: int = 10,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        enable_rerank: bool = True,
    ) -> List[Document]:
        """
        執行混合檢索（實作 BaseRetriever 介面）

        流程：
        1. 並行執行向量檢索 + BM25 檢索（各取 top_k * 2 確保召回率）
        2. RRF 融合結果
        3. 多重表徵去重
        4. BGE 重排序（可選）
        5. 返回 top_k 結果

        Args:
            query: 查詢文本
            collection_id: Collection ID
            top_k: 返回結果數量
            vector_weight: 向量檢索權重（預設 0.5）
            bm25_weight: BM25 檢索權重（預設 0.5）
            enable_rerank: 是否啟用重排序（預設 True）

        Returns:
            檢索結果列表（Document 物件）
        """
        logger.info(
            f"開始混合檢索: collection_{collection_id}, "
            f"query='{query[:50]}...', top_k={top_k}"
        )

        # 並行執行向量檢索 + BM25 檢索（各取 top_k * 2 確保召回率）
        vector_results, bm25_results = await asyncio.gather(
            self.vector_retriever.search(query, collection_id, top_k * 2),
            self.bm25_retriever.search(query, collection_id, top_k * 2),
        )

        logger.debug(
            f"向量檢索: {len(vector_results)} 個結果, "
            f"BM25 檢索: {len(bm25_results)} 個結果"
        )

        # RRF 融合
        fused_results = self._rrf_fusion(
            vector_results,
            bm25_results,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight
        )

        # 多重表徵去重
        deduplicated = self._deduplicate_multirepresentation(fused_results)

        # BGE 重排序（可選）
        if enable_rerank and self.reranker and deduplicated:
            reranked = await self._rerank_with_bge(query, deduplicated, top_k)
            logger.info(
                f"混合檢索完成 (含重排序): 返回 {len(reranked)} 個結果"
            )
            return reranked
        else:
            final_results = deduplicated[:top_k]

            # 轉換 RRF 分數到 [0, 1] 範圍（根據配置）
            if self.rrf_score_normalization:
                for doc in final_results:
                    # 保留原始 RRF 分數到 metadata (供調試)
                    doc.metadata["rrf_score"] = doc.score
                    # 轉換為正規化分數
                    doc.score = self._normalize_rrf_score(doc.score)

            # 說明 : 根據 "跨 Collection 檢索" 流程, 現在重排序只會在各別子查詢的所有 Collection 檢索結果合併後, 進行該子查詢一次性的重排序, 然後最終合併所有子查詢的時候不會再次進行重排序
            # logger.info(
            #     f"混合檢索完成 (無重排序): 返回 {len(final_results)} 個結果"
            # )
            return final_results

    def _rrf_fusion(
        self,
        vector_results: List[Document],
        bm25_results: List[Document],
        k: int = 60,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ) -> List[Document]:
        """
        Reciprocal Rank Fusion (RRF) 融合算法

        RRF 公式: score(d) = Σ [w / (k + rank(d))]

        設計說明：
        - RRF 是一種無參數的排名融合方法，不依賴原始分數
        - 使用排名位置計算融合分數，對不同檢索器的分數尺度不敏感
        - k 參數用於平滑排名差異（預設 60）

        Args:
            vector_results: 向量檢索結果
            bm25_results: BM25 檢索結果
            k: RRF 常數（預設 60）
            vector_weight: 向量檢索權重
            bm25_weight: BM25 檢索權重

        Returns:
            融合後的結果（按分數排序）
        """
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        # 向量檢索結果的 RRF 分數
        for rank, doc in enumerate(vector_results, start=1):
            rrf_scores[doc.id] = rrf_scores.get(doc.id, 0) + \
                (vector_weight / (k + rank))
            doc_map[doc.id] = doc

        # BM25 檢索結果的 RRF 分數
        for rank, doc in enumerate(bm25_results, start=1):
            rrf_scores[doc.id] = rrf_scores.get(doc.id, 0) + \
                (bm25_weight / (k + rank))
            if doc.id not in doc_map:
                doc_map[doc.id] = doc

        # 按 RRF 分數排序
        sorted_ids = sorted(
            rrf_scores.keys(),
            key=lambda x: rrf_scores[x],
            reverse=True
        )

        # 更新分數並返回
        fused_results = []
        for doc_id in sorted_ids:
            doc = doc_map[doc_id]
            doc.score = rrf_scores[doc_id]
            fused_results.append(doc)

        logger.debug(f"RRF 融合完成: {len(fused_results)} 個結果")
        return fused_results

    def _deduplicate_multirepresentation(
        self,
        documents: List[Document]
    ) -> List[Document]:
        """
        多重表徵去重

        重要：qa_id 只在單個 Dataset 內唯一，不是全局唯一！
        因此分組鍵必須是 (dataset_id, qa_id) 的複合鍵

        設計說明：
        - 同一個 Dataset 的同一個 QA 組的多個表徵 (question, answer, summary) 才會合併
        - 不同 Dataset 的相同 qa_id 是完全獨立的 QA 組，不會合併
        - 保留分數最高的表徵
        - 智能回填機制：如果選中的是 "question" 表徵但有 answer，則回填完整內容
        - 其他表徵合併到 metadata 中以保留完整資訊

        範例：
        - D1 的 qa_001 和 D2 的 qa_001 是兩個完全不同的 QA 組
        - 只有 D1 的 qa_001 的 question/answer/summary 才會合併

        Args:
            documents: 待去重的文檔列表

        Returns:
            去重後的文檔列表
        """
        qa_groups: Dict[str, List[Document]] = {}
        non_qa_docs = []

        # 分組（使用複合鍵）
        for doc in documents:
            dataset_id = doc.metadata.get("dataset_id")
            qa_id = doc.metadata.get("qa_id")

            if dataset_id is not None and qa_id:
                # 複合鍵：確保只有同一個 Dataset 的同一個 QA 組才會合併
                group_key = f"dataset_{dataset_id}_qa_{qa_id}"
                if group_key not in qa_groups:
                    qa_groups[group_key] = []
                qa_groups[group_key].append(doc)
            else:
                non_qa_docs.append(doc)

        # 去重：每組保留分數最高的
        deduplicated = []
        for group_key, group in qa_groups.items():
            # 按分數排序
            group.sort(key=lambda x: x.score, reverse=True)
            best_doc = group[0]

            # 智能回填機制：如果選中的是 "question" 表徵，但 metadata 中有 answer，則回填完整內容
            if best_doc.metadata.get("representation") == "question":
                question = best_doc.metadata.get("question", "").strip()
                answer = best_doc.metadata.get("answer", "").strip()

                if question and answer:
                    # 重構為完整 Q+A 格式
                    best_doc.content = f"Q: {question}\nA: {answer}"
                    best_doc.metadata["representation"] = "full_reconstructed"  # 標記為回填
                    logger.debug(
                        f"智能回填: {group_key} 從 'question' 表徵回填為完整 Q+A"
                    )

            # 其他表徵資訊合併到 metadata
            other_representations = [
                {
                    "representation": doc.metadata.get("representation"),
                    "content": doc.content,
                    "score": doc.score
                }
                for doc in group[1:]
            ]

            if other_representations:
                best_doc.metadata["other_representations"] = other_representations

            deduplicated.append(best_doc)

        # 加入非 QA 文檔
        deduplicated.extend(non_qa_docs)

        # 重新排序
        deduplicated.sort(key=lambda x: x.score, reverse=True)

        logger.debug(f"多表徵去重完成: {len(documents)} → {len(deduplicated)} 個結果")
        return deduplicated

    def _normalize_reranker_score(self, logits: float) -> float:
        """
        將 BGE Reranker 的 logits 轉換為機率分數 [0, 1]

        理論依據:
        BGE Reranker 是 Cross-Encoder 模型,輸出的 logits 在訓練時使用
        Binary Cross-Entropy Loss,應透過 Sigmoid 函數轉換為機率分數。

        轉換公式: P(相關) = σ(logit) = 1 / (1 + e^(-logit))

        Args:
            logits: Reranker 輸出的原始 logits

        Returns:
            相關性機率分數,範圍 [0, 1]

        轉換效果範例:
            - logits 5.0  → 0.9933 (99.33% 相關)
            - logits 2.0  → 0.8808 (88.08% 相關)
            - logits 0.0  → 0.5000 (50.00% 相關)
            - logits -2.0 → 0.1192 (11.92% 相關)
            - logits -5.0 → 0.0067 (0.67% 相關)
        """
        return 1.0 / (1.0 + math.exp(-logits))

    def _normalize_rrf_score(self, rrf_score: float) -> float:
        """
        將 RRF 融合分數轉換為 [0, 1] 範圍的相關性分數

        使用調整後的 Sigmoid 轉換,使 RRF 分數與 Reranker 分數
        保持一致的尺度和解釋性。

        轉換公式: score = 1 / (1 + e^(-scale * (rrf_score - shift)))

        Args:
            rrf_score: RRF 融合後的原始分數 (典型範圍 0.007-0.017)

        Returns:
            相關性分數,範圍 [0, 1],可視為百分比

        設計依據:
            - scale = 1000: 放大小數值,使 sigmoid 有效區分
            - shift = 0.012: 設為 RRF 典型範圍的中點 (輸出 0.5)
            - 轉換後,高 RRF 分數 (0.016+) → 99%+,低分數 (0.007-) → 1%-

        轉換效果範例:
            - RRF 0.0164 (rank=1, 雙來源) → 0.9933 (99.33% 相關)
            - RRF 0.0140 (rank=5, 雙來源) → 0.9179 (91.79% 相關)
            - RRF 0.0120 (中位數)         → 0.5000 (50.00% 相關)
            - RRF 0.0090 (rank=5, 單來源) → 0.0474 (4.74% 相關)
            - RRF 0.0071 (rank=10, 單來源)→ 0.0067 (0.67% 相關)
        """
        return 1.0 / (
            1.0 + math.exp(-self.rrf_sigmoid_scale * (rrf_score - self.rrf_sigmoid_shift))
        )

    async def _rerank_with_bge(
        self,
        query: str,
        documents: List[Document],
        top_k: int
    ) -> List[Document]:
        """
        使用 BGE Reranker 重排序

        設計說明：
        - 使用 RerankerModel 的模型池進行並發安全的重排序
        - 重排序可以提升跨領域檢索的準確性
        - 注意 : 前面的檢索階段的分數或RRF融合分數將被 Reranker 的重排序分數覆蓋

        Args:
            query: 查詢文本
            documents: 待重排序的文檔
            top_k: 返回結果數量

        Returns:
            重排序後的文檔列表
        """
        if not documents:
            return []

        if not self.reranker:
            logger.warning("Reranker 未啟用，跳過重排序")
            return documents[:top_k]

        try:
            # 準備文檔文本
            doc_texts = [doc.content for doc in documents]

            # 執行重排序（使用模型池，支援並發）
            rerank_results = await self.reranker.rerank(
                query=query,
                documents=doc_texts,
                top_k=top_k
            )

            # 更新分數並重排
            reranked_docs = []
            for idx, logits in rerank_results:
                doc = documents[idx]

                # 保留原始 logits 到 metadata (供調試)
                doc.metadata["reranker_logits"] = logits

                # 根據配置決定是否轉換分數
                if self.reranker_score_normalization:
                    doc.score = self._normalize_reranker_score(logits)
                else:
                    doc.score = logits

                reranked_docs.append(doc)

            logger.debug(f"BGE 重排序完成: {len(reranked_docs)} 個結果")
            return reranked_docs

        except Exception as e:
            logger.error(f"BGE 重排序失敗: {e}")
            return documents[:top_k]
