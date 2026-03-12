# -*- coding: utf-8 -*-
"""
BM25 檢索器
實作惰性載入、事件驅動失效、線程安全的 BM25 索引管理與檢索
"""
from typing import Dict, Tuple, List
import asyncio
from collections import OrderedDict
from rank_bm25 import BM25Okapi
from loguru import logger
import jieba
import re

from app.modules.retrieval.retrievers.base import BaseRetriever
from app.modules.retrieval.schemas import Document
from app.vector_stores.base import BaseVectorStore


class BM25Retriever(BaseRetriever):
    """
    BM25 檢索器（含索引管理）

    職責：
    1. BM25 索引管理（惰性載入、事件驅動失效、LRU 快取）
    2. 中英文分詞
    3. BM25 關鍵字檢索

    設計原則：
    1. 惰性載入: 索引在第一次使用時才建立
    2. 自動失效: 資料變更時自動更新索引
    3. 線程安全: 使用 asyncio.Lock 保護並發訪問
    4. LRU 快取: 限制快取索引數量

    ⚠️ 並發安全修復：
    - 修復 1：快取命中路徑使用全局鎖（防止 OrderedDict 競爭）
    - 修復 2：LRU 淘汰使用全局鎖（防止多協程同時淘汰導致 KeyError）
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        max_cache_size: int = 50
    ):
        """
        初始化 BM25Retriever

        Args:
            vector_store: 向量資料庫實例
            max_cache_size: 最大快取索引數量 (LRU)
        """
        self.vector_store = vector_store
        self.max_cache_size = max_cache_size

        # 使用 OrderedDict 實作 LRU
        self._indices: OrderedDict[str, BM25Okapi] = OrderedDict()
        self._corpus_cache: OrderedDict[str, List[dict]] = OrderedDict()

        # 每個 collection 一個鎖（用於索引建立）
        self._locks: Dict[str, asyncio.Lock] = {}
        # 全局鎖（用於快取操作和 LRU 淘汰）
        self._global_lock = asyncio.Lock()

    async def search(
        self,
        query: str,
        collection_id: int,
        top_k: int = 10
    ) -> List[Document]:
        """
        執行 BM25 檢索（實作 BaseRetriever 介面）

        Args:
            query: 查詢文本
            collection_id: Collection ID
            top_k: 返回結果數量

        Returns:
            檢索結果列表（Document 物件）
        """
        # 取得索引 (惰性載入)
        bm25_index, corpus = await self.get_index(collection_id)

        if not corpus:
            logger.warning(f"Collection {collection_id} 沒有文檔")
            return []

        # 分詞查詢
        tokenized_query = self._tokenize(query)

        if not tokenized_query:
            logger.warning(f"查詢分詞結果為空: {query}")
            return []

        # 計算 BM25 分數
        scores = bm25_index.get_scores(tokenized_query)

        # 排序並取 top_k
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # 組合結果並轉換為 Document（過濾無關結果）
        results = [
            Document(
                id=corpus[idx]["id"],
                content=corpus[idx]["document"],
                metadata=corpus[idx]["metadata"],
                score=float(scores[idx])
            )
            for idx in top_indices
            if scores[idx] > 0
        ]

        logger.debug(
            f"BM25 檢索完成: collection_{collection_id}, "
            f"返回 {len(results)} 個結果"
        )

        return results

    async def get_index(
        self,
        collection_id: int
    ) -> Tuple[BM25Okapi, List[dict]]:
        """
        取得 BM25 索引 (惰性載入)

        Args:
            collection_id: Collection ID

        Returns:
            (BM25 索引, 文檔列表)

        Raises:
            RuntimeError: 向量資料庫 Collection 不存在
        """
        collection_name = f"collection_{collection_id}"

        # ✅ 修復 1：快取命中路徑使用全局鎖保護
        # 原因：多個協程同時調用 move_to_end() 會導致 OrderedDict 內部狀態損壞
        async with self._global_lock:
            if collection_name in self._indices:
                logger.debug(f"BM25 索引命中快取: {collection_name}")
                # 移到最後 (標記為最近使用)
                self._indices.move_to_end(collection_name)
                self._corpus_cache.move_to_end(collection_name)
                return self._indices[collection_name], self._corpus_cache[collection_name]

            # 取得或建立 collection 專屬的鎖
            if collection_name not in self._locks:
                self._locks[collection_name] = asyncio.Lock()

        # 建立索引 (使用 per-collection 鎖)
        async with self._locks[collection_name]:
            # 雙重檢查（避免重複建立）
            async with self._global_lock:
                if collection_name in self._indices:
                    self._indices.move_to_end(collection_name)
                    self._corpus_cache.move_to_end(collection_name)
                    return self._indices[collection_name], self._corpus_cache[collection_name]

            logger.info(f"開始建立 BM25 索引: {collection_name}")
            index, corpus = await self._build_index(collection_id)

            # ✅ 修復 2：LRU 淘汰和快取索引使用全局鎖保護
            # 原因：多個不同 collection 的協程同時觸發 LRU 淘汰會導致 KeyError
            async with self._global_lock:
                # 再次檢查快取大小（避免過度淘汰）
                if len(self._indices) >= self.max_cache_size:
                    oldest_key = next(iter(self._indices))
                    del self._indices[oldest_key]
                    del self._corpus_cache[oldest_key]
                    # 同時刪除對應的鎖（可選）
                    if oldest_key in self._locks:
                        del self._locks[oldest_key]
                    logger.info(f"LRU 淘汰索引: {oldest_key}")

                # 快取索引
                self._indices[collection_name] = index
                self._corpus_cache[collection_name] = corpus

            logger.info(
                f"✅ BM25 索引建立完成: {collection_name} "
                f"({len(corpus)} 個文檔)"
            )
            return index, corpus

    async def _build_index(
        self,
        collection_id: int
    ) -> Tuple[BM25Okapi, List[dict]]:
        """
        從向量資料庫建立 BM25 索引

        Args:
            collection_id: Collection ID

        Returns:
            (BM25 索引, 文檔列表)
        """
        collection_name = f"collection_{collection_id}"

        try:
            # 從向量資料庫取得 Collection
            vector_collection = await self.vector_store.get_collection(
                name=collection_name
            )

            # 取得所有文檔
            results = await vector_collection.get(
                include=["documents", "metadatas"]
            )

            if not results.documents:
                logger.warning(
                    f"Collection {collection_id} 沒有文檔，建立空索引"
                )
                return BM25Okapi([[]]), []

            # 分詞
            tokenized_corpus = [
                self._tokenize(doc) for doc in results.documents
            ]

            # 建立 BM25 索引
            bm25_index = BM25Okapi(tokenized_corpus)

            # 組合文檔資訊 (用於結果映射)
            corpus = [
                {
                    "id": results.ids[i],
                    "document": results.documents[i],
                    "metadata": results.metadatas[i] if results.metadatas else {}
                }
                for i in range(len(results.documents))
            ]

            return bm25_index, corpus

        except Exception as e:
            logger.error(f"建立 BM25 索引失敗: {e}")
            raise RuntimeError(f"無法建立 BM25 索引: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """
        分詞函式 - 支援中英文

        Args:
            text: 待分詞文本

        Returns:
            分詞結果
        """
        # 英文單詞 (小寫化)
        words = re.findall(r'\b\w+\b', text.lower())

        # 中文分詞 (提取中文部分)
        chinese_text = re.sub(r'[a-zA-Z0-9\s]', '', text)
        if chinese_text:
            chinese_words = list(jieba.cut_for_search(chinese_text))
        else:
            chinese_words = []

        return words + chinese_words

    async def invalidate_collection(self, collection_id: int) -> None:
        """
        使 Collection 的索引失效

        使用場景:
        - 新增 Dataset (上傳檔案並向量化)
        - 刪除 Dataset
        - 更新 Collection 設定

        Args:
            collection_id: Collection ID
        """
        collection_name = f"collection_{collection_id}"

        async with self._global_lock:
            if collection_name in self._indices:
                del self._indices[collection_name]
                del self._corpus_cache[collection_name]
                logger.info(f"已使 BM25 索引失效: {collection_name}")
            else:
                logger.debug(f"索引不存在,無需失效: {collection_name}")

    async def clear_cache(self) -> None:
        """清空所有快取"""
        async with self._global_lock:
            self._indices.clear()
            self._corpus_cache.clear()
            logger.info("已清空所有 BM25 索引快取")

    def get_cache_stats(self) -> dict:
        """
        取得快取統計資訊

        Returns:
            {"cached_collections": [...], "cache_size": ..., "max_size": ...}
        """
        return {
            "cached_collections": list(self._indices.keys()),
            "cache_size": len(self._indices),
            "max_size": self.max_cache_size
        }
