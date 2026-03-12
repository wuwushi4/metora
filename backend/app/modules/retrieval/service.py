# -*- coding: utf-8 -*-
"""
檢索服務層
實作跨 Collection 檢索協調邏輯
"""
from typing import List
import asyncio
import json
from loguru import logger

from app.modules.retrieval.retrievers.hybrid import HybridRetriever
from app.modules.retrieval.schemas import Document


class RetrievalService:
    """
    檢索服務 - 跨 Collection 檢索協調層

    職責：
    1. 跨 Collection 檢索協調（多查詢 × 多 Collections）
    2. 單一 Collection 檢索委託給 HybridRetriever

    設計原則：
    1. 無狀態：不維護檢索相關的狀態
    2. 單一職責：只負責跨 Collection 協調，不處理具體檢索邏輯
    3. 依賴注入：接受 HybridRetriever
    """

    def __init__(self, hybrid_retriever: HybridRetriever):
        """
        初始化檢索服務

        Args:
            hybrid_retriever: 混合檢索器（已整合向量、BM25、RRF、去重、重排序）
        """
        self.hybrid_retriever = hybrid_retriever

    async def hybrid_search_single_collection(
        self,
        query: str,
        collection_id: int,
        top_k: int = 3,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ) -> List[Document]:
        """
        單一 Collection 的混合檢索（委託給 HybridRetriever）

        Args:
            query: 查詢文本
            collection_id: Collection ID
            top_k: 返回結果數量
            vector_weight: 向量檢索權重
            bm25_weight: BM25 檢索權重

        Returns:
            文檔列表（metadata 已清理和反序列化）
        """
        results = await self.hybrid_retriever.search(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            enable_rerank=True
        )

        # 清理和反序列化 metadata
        for doc in results:
            doc.metadata = self._clean_metadata(doc.metadata)

        return results

    async def cross_collection_search(
        self,
        queries: List[str],
        collection_ids: List[int],
        top_k: int = 3,
    ) -> List[Document]:
        """
        跨 Collection 檢索 - 完整流程

        流程說明:
        假設 queries = [Q1, Q2], collection_ids = [C1, C2]

        Q1 (子查詢1):
        ├── C1_檢索 → 混合檢索 → RRF融合 → 去重 → Q1_C1_top3
        ├── C2_檢索 → 混合檢索 → RRF融合 → 去重 → Q1_C2_top3
        └── 合併: [Q1_C1_top3 + Q1_C2_top3] → BGE重排序 → Q1_final_top3

        Q2 (子查詢2):
        ├── C1_檢索 → 混合檢索 → RRF融合 → 去重 → Q2_C1_top3
        ├── C2_檢索 → 混合檢索 → RRF融合 → 去重 → Q2_C2_top3
        └── 合併: [Q2_C1_top3 + Q2_C2_top3] → BGE重排序 → Q2_final_top3

        最終合併 Q1_final_top3 + Q2_final_top3 (不再排序)

        Args:
            queries: 子查詢列表 (來自查詢重構)
            collection_ids: 目標 Collection IDs
            top_k: 每個子查詢返回結果數量

        Returns:
            最終文檔列表（metadata 已清理和反序列化）
        """
        logger.info(
            f"開始跨 Collection 檢索: "
            f"{len(queries)} 個查詢 x {len(collection_ids)} 個 Collections"
        )

        all_final_results = []

        # 並行處理所有子查詢
        query_tasks = [
            self._process_single_query(q, collection_ids, top_k)
            for q in queries
        ]

        query_results = await asyncio.gather(*query_tasks)

        # 合併所有子查詢的結果 (不再排序)
        for results in query_results:
            all_final_results.extend(results)

        # 清理和反序列化 metadata（重要：處理向量資料庫的 JSON 字串字段）
        for doc in all_final_results:
            doc.metadata = self._clean_metadata(doc.metadata)

        logger.info(
            f"跨 Collection 檢索完成: 返回 {len(all_final_results)} 個結果"
        )

        return all_final_results

    async def get_articles_by_nums(
        self,
        article_nums: List[str],
        collection_ids: List[int],
        chunk_type: str = "regulation_article"
    ) -> List[Document]:
        """
        直接通過條文編號查詢法條（純 metadata 查詢，不使用向量檢索）

        適用場景：
        - 引用關係擴展（已知確切的條文編號）
        - 條文比對
        - 精確查詢

        流程說明：
        - 不執行向量檢索、BM25 檢索、RRF 融合、重排序等流程
        - 直接使用向量資料庫的 metadata 過濾功能
        - 效能：約 2ms/條文（vs 向量檢索的 200ms/條文）

        Args:
            article_nums: 條文編號列表（如 ["3", "25-1", "10"]）
            collection_ids: Collection IDs 列表
            chunk_type: 分塊類型（預設 "regulation_article"）

        Returns:
            Document 列表（metadata 已清理和反序列化）
        """
        logger.info(
            f"[RetrievalService] 直接查詢條文：{len(article_nums)} 個條文編號 × "
            f"{len(collection_ids)} 個 Collections"
        )

        all_docs = []

        for collection_id in collection_ids:
            try:
                vector_collection = await self.hybrid_retriever.vector_retriever.vector_store.get_collection(
                    name=f"collection_{collection_id}"
                )

                for article_num in article_nums:
                    # 查詢條件：article_num + chunk_type
                    # 使用向量資料庫的 metadata 過濾功能（不需要向量檢索）
                    results = await vector_collection.get(
                        where={
                            "$and": [
                                {"article_num": {"$eq": article_num}},
                                {"chunk_type": {"$eq": chunk_type}}
                            ]
                        },
                        include=["documents", "metadatas"]
                    )

                    if results.ids:
                        # 找到法條，創建 Document 對象
                        doc = Document(
                            id=results.ids[0],
                            content=results.documents[0] if results.documents else "",
                            metadata=self._clean_metadata(results.metadatas[0] if results.metadatas else {}),
                            score=1.0  # 精確匹配，設為滿分
                        )
                        all_docs.append(doc)
                        logger.debug(
                            f"[RetrievalService] ✓ 找到第 {article_num} 條 "
                            f"(collection_{collection_id})"
                        )
                    else:
                        logger.warning(
                            f"[RetrievalService] ✗ 找不到第 {article_num} 條 "
                            f"(collection_{collection_id})"
                        )

            except Exception as e:
                logger.error(
                    f"[RetrievalService] 查詢 collection_{collection_id} 失敗: {e}"
                )
                continue

        logger.info(
            f"[RetrievalService] 直接查詢完成：返回 {len(all_docs)}/{len(article_nums)} 個條文"
        )

        return all_docs

    async def _process_single_query(
        self,
        query: str,
        collection_ids: List[int],
        top_k: int
    ) -> List[Document]:
        """
        處理單一子查詢的所有 Collections

        流程：
        1. 並行檢索所有 Collections（禁用重排序）
        2. 合併結果
        3. 【關鍵】替換情境分塊為法條原文（僅法規檢索）
        4. 統一進行 BGE 重排序（使用法條原文）
        5. 返回 top_k
        """
        logger.debug(f"處理子查詢: '{query[:50]}...'")

        # 並行檢索所有 Collections（禁用重排序，稍後統一重排）
        collection_tasks = [
            self.hybrid_retriever.search(
                query=query,
                collection_id=coll_id,
                top_k=top_k,
                enable_rerank=False  # 關鍵：先不重排序
            )
            for coll_id in collection_ids
        ]

        collection_results = await asyncio.gather(*collection_tasks)

        # 合併所有 Collection 的結果
        merged_docs = []
        for results in collection_results:
            merged_docs.extend(results)

        if not merged_docs:
            logger.warning(f"子查詢無結果: '{query[:50]}...'")
            return []

        # 【關鍵步驟】替換情境分塊為法條原文（僅影響法規檢索）
        # 這確保 BGE 重排序使用的是法條原文而非情境描述
        merged_docs = await self._replace_scenario_with_article_multi_collections(
            merged_docs,
            collection_ids
        )

        # 統一進行 BGE 重排序（使用 HybridRetriever 的內部方法）
        # 現在 BGE 使用的是法條原文，而不是情境描述
        reranked = await self.hybrid_retriever._rerank_with_bge(
            query, merged_docs, top_k
        )

        logger.debug(
            f"子查詢完成: 返回 {len(reranked)} 個結果"
        )
        return reranked

    async def _replace_scenario_with_article(
        self,
        documents: List[Document],
        collection_id: int
    ) -> List[Document]:
        """
        將情境分塊替換為對應的法條原文分塊

        【適用範圍】僅處理 chunk_type == "regulation_scenario" 的分塊
        【其他分塊】QA、文檔、一般法規等完全不受影響

        Args:
            documents: 檢索結果列表
            collection_id: Collection ID

        Returns:
            處理後的文檔列表（情境分塊已替換為法條原文）
        """
        # 第一步：檢查是否有情境分塊
        scenario_docs = [
            doc for doc in documents
            if doc.metadata.get("chunk_type") == "regulation_scenario"
        ]

        if not scenario_docs:
            # 沒有情境分塊，直接返回（不影響其他 RAG）
            logger.debug("[RetrievalService] 無情境分塊，跳過替換邏輯")
            return documents

        logger.info(
            f"[RetrievalService] 檢測到 {len(scenario_docs)} 個情境分塊，"
            f"準備替換為法條原文"
        )

        # 第二步：收集需要獲取的法條編號
        article_nums_to_fetch = set()
        for doc in scenario_docs:
            linked_article = doc.metadata.get("linked_article")
            if linked_article:
                article_nums_to_fetch.add(linked_article)

        if not article_nums_to_fetch:
            logger.warning("[RetrievalService] 情境分塊缺少 linked_article，無法替換")
            return documents

        # 第三步：查詢向量資料庫獲取對應的法條原文分塊
        try:
            vector_collection = await self.hybrid_retriever.vector_retriever.vector_store.get_collection(
                name=f"collection_{collection_id}"
            )

            article_docs = {}
            for article_num in article_nums_to_fetch:
                # 查詢條件：article_num + chunk_type == "regulation_article"
                results = await vector_collection.get(
                    where={
                        "$and": [
                            {"article_num": {"$eq": article_num}},
                            {"chunk_type": {"$eq": "regulation_article"}}
                        ]
                    },
                    include=["documents", "metadatas"]
                )

                if results.ids:
                    # 找到法條原文分塊
                    article_docs[article_num] = Document(
                        id=results.ids[0],
                        content=results.documents[0] if results.documents else "",
                        metadata=results.metadatas[0] if results.metadatas else {},
                        score=1.0  # 直接查詢，設為滿分
                    )
                    logger.debug(
                        f"[RetrievalService] 成功獲取第 {article_num} 條法條原文"
                    )

        except Exception as e:
            logger.error(f"[RetrievalService] 查詢法條原文失敗: {e}")
            return documents

        # 第四步：替換情境分塊為法條原文分塊
        final_docs = []
        replaced_count = 0

        for doc in documents:
            if doc.metadata.get("chunk_type") == "regulation_scenario":
                # 這是情境分塊，嘗試替換
                linked_article = doc.metadata.get("linked_article")
                if linked_article in article_docs:
                    # 替換為法條原文分塊
                    final_docs.append(article_docs[linked_article])
                    replaced_count += 1
                    logger.debug(
                        f"[RetrievalService] 情境分塊已替換為第 {linked_article} 條原文"
                    )
                else:
                    # 找不到對應的法條原文，保留情境分塊但記錄警告
                    logger.warning(
                        f"[RetrievalService] 找不到第 {linked_article} 條的法條原文，"
                        f"保留情境分塊"
                    )
                    final_docs.append(doc)
            else:
                # 不是情境分塊，直接保留（QA、文檔、法規原文等）
                final_docs.append(doc)

        logger.info(
            f"[RetrievalService] 情境分塊替換完成: "
            f"{replaced_count}/{len(scenario_docs)} 個成功替換"
        )

        return final_docs

    async def _replace_scenario_with_article_multi_collections(
        self,
        documents: List[Document],
        collection_ids: List[int]
    ) -> List[Document]:
        """
        處理多 Collection 情況的情境分塊替換

        需要根據每個 document 的 collection_id 查詢對應的向量資料庫

        Args:
            documents: 檢索結果列表
            collection_ids: Collection IDs 列表

        Returns:
            處理後的文檔列表
        """
        # 檢查是否有情境分塊
        scenario_docs = [
            doc for doc in documents
            if doc.metadata.get("chunk_type") == "regulation_scenario"
        ]

        if not scenario_docs:
            return documents

        # 按 collection_id 分組
        docs_by_collection = {}
        for doc in documents:
            coll_id = doc.metadata.get("collection_id")
            if coll_id not in docs_by_collection:
                docs_by_collection[coll_id] = []
            docs_by_collection[coll_id].append(doc)

        # 對每個 collection 分別處理
        final_docs = []
        for coll_id, coll_docs in docs_by_collection.items():
            processed_docs = await self._replace_scenario_with_article(
                coll_docs,
                coll_id
            )
            final_docs.extend(processed_docs)

        return final_docs

    def _clean_metadata(self, metadata: dict) -> dict:
        """
        清理 metadata，移除冗餘或內部字段，並反序列化 JSON 字串字段

        保留：
        - 溯源信息：collection_id, dataset_id, dataset_filename, qa_id
        - 展示信息：category, keywords, representation
        - 額外上下文：other_representations
        - 法規信息：law_name, article_num, chapter_num, references_to, referenced_by 等

        移除：
        - 內部字段：chunk_index
        - JSON 字串：qa_metadata, file_metadata
        - 冗餘字段：collection_name
        - 重複內容：question, answer（已在 content 中）

        特殊處理：
        - 反序列化 JSON 字串字段（向量資料庫不支援 list/dict 類型）

        Args:
            metadata: 原始 metadata

        Returns:
            清理後的 metadata
        """
        # 第一步：提取基本字段
        cleaned = {
            # 溯源信息
            "collection_id": metadata.get("collection_id"),
            "dataset_id": metadata.get("dataset_id"),
            "dataset_filename": metadata.get("dataset_filename"),
            "qa_id": metadata.get("qa_id"),

            # 展示信息
            "category": metadata.get("category"),
            "representation": metadata.get("representation"),

            # 額外上下文
            "other_representations": metadata.get("other_representations"),
        }

        # 第二步：反序列化需要特殊處理的 JSON 字串字段
        # 這些字段在 vectorization.py 中被序列化為 JSON 字串（因為向量資料庫不支援 list/dict）
        json_fields = ["keywords", "references_to", "referenced_by"]

        for field in json_fields:
            if field in metadata:
                value = metadata[field]

                # 記錄原始值的類型（用於調試）
                if field in ["references_to", "referenced_by"]:
                    logger.debug(
                        f"[RetrievalService] 處理 {field}: "
                        f"類型={type(value).__name__}, 值={repr(value)[:100]}"
                    )

                # 如果已經是列表或字典，直接使用
                if isinstance(value, (list, dict)):
                    cleaned[field] = value
                    if field in ["references_to", "referenced_by"]:
                        logger.debug(
                            f"[RetrievalService] {field} 已是列表/字典: {value}"
                        )
                    continue

                # 如果是字串，嘗試反序列化
                if isinstance(value, str) and value.strip():
                    try:
                        # 嘗試 JSON 解析（處理 '["item1", "item2"]' 格式）
                        if value.startswith("[") or value.startswith("{"):
                            cleaned[field] = json.loads(value)
                            # logger.debug(
                            #     f"[RetrievalService] JSON 反序列化成功: {field} = {value[:50]}... → {cleaned[field]}"
                            # )
                        # 處理逗號分隔格式
                        elif "," in value and field == "keywords":
                            cleaned[field] = [k.strip() for k in value.split(",") if k.strip()]
                            # logger.debug(
                            #     f"[RetrievalService] 逗號分隔解析成功: {field} = {value[:50]}... → {cleaned[field]}"
                            # )
                        else:
                            # 單個值也保留
                            cleaned[field] = value
                            if field in ["references_to", "referenced_by"]:
                                logger.debug(
                                    f"[RetrievalService] {field} 保留為原始字串: {value}"
                                )
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"[RetrievalService] JSON 反序列化失敗: {field} = '{value[:50]}...', "
                            f"錯誤: {e}. 保留原始字串。"
                        )
                        cleaned[field] = value
                else:
                    # 空字串或空值，記錄一下
                    if field in ["references_to", "referenced_by"]:
                        logger.debug(
                            f"[RetrievalService] {field} 為空字串或無值，跳過"
                        )

        # 第三步：保留所有法規相關字段（原樣傳遞）
        # 注意：references_to 和 referenced_by 已在第二步處理，不要重複
        regulation_fields = [
            "law_name", "law_code", "law_category",
            "chapter_num", "chapter_name", "chapter_display",
            "article_num", "article_display", "has_items", "item_count",
            "hierarchy_path", "full_path", "has_references",
            "chunk_type", "chunk_index", "linked_article",
            "source_url", "article_url", "last_updated",
            "scenario_text"
        ]

        for field in regulation_fields:
            if field in metadata and field not in cleaned:
                # 只添加尚未處理的字段（避免覆蓋已反序列化的字段）
                cleaned[field] = metadata[field]

        # 移除 None 值
        return {k: v for k, v in cleaned.items() if v is not None}
