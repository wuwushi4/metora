# -*- coding: utf-8 -*-
"""
Retrieval API 路由
提供檢索服務的 REST API
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from app.modules.retrieval.service import RetrievalService
from app.modules.retrieval.schemas import (
    SearchRequest,
    SearchResult,
    DocumentResponse,
)
from app.core.dependencies import get_retrieval_service
from app.i18n import t
from app.utils.response import success_response, ApiResponse

router = APIRouter(prefix="/retrieval", tags=["檢索"])


@router.post(
    "/search",
    response_model=ApiResponse[SearchResult],
    summary="混合檢索",
    description="執行混合檢索 (向量 + BM25 + RRF 融合 + 多重表徵去重 + BGE重排序)"
)
async def search(
    request: SearchRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    混合檢索端點

    流程:
    1. 並行執行向量檢索和BM25關鍵字檢索
    2. 使用RRF算法融合兩種檢索結果
    3. 多重表徵去重 (保留分數最高的表徵)
    4. 可選BGE重排序
    5. 返回top_k結果

    特性:
    - 支援跨 Collection 檢索
    - 自動執行 RRF 融合
    - 可選 BGE 重排序
    """
    # 執行檢索
    documents = await retrieval_service.cross_collection_search(
        queries=[request.query],
        collection_ids=request.collection_ids,
        top_k=request.top_k,
    )

    # 轉換為響應格式（清理 metadata）
    doc_responses = [
        DocumentResponse(
            id=doc.id,
            content=doc.content,
            score=doc.score,
            metadata=retrieval_service._clean_metadata(doc.metadata)
        )
        for doc in documents
    ]

    result = SearchResult(
        query=request.query,
        results=doc_responses,
        total=len(doc_responses)
    )

    return success_response(
        data=result,
        message=t('retrieval.searchComplete')
    )


@router.get(
    "/test/{collection_id}",
    summary="測試單一 Collection 檢索",
    description="用於測試和除錯"
)
async def test_search(
    collection_id: int,
    query: str = Query(..., description="查詢文本"),
    top_k: int = Query(default=5, ge=1, le=20, description="返回結果數量"),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    測試端點 - 單一 Collection 混合檢索

    用於:
    - 測試檢索功能
    - 除錯檢索結果
    - 驗證索引是否正確建立
    """
    documents = await retrieval_service.hybrid_search_single_collection(
        query=query,
        collection_id=collection_id,
        top_k=top_k,
    )

    return success_response(
        data={
            "query": query,
            "collection_id": collection_id,
            "results": [doc.to_dict() for doc in documents],
            "total": len(documents)
        },
        message=t('retrieval.testComplete')
    )


@router.get(
    "/bm25/stats",
    summary="BM25 索引統計",
    description="查看 BM25 索引快取狀態"
)
async def bm25_stats(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    取得 BM25 索引管理器的快取統計資訊

    返回:
    - cached_collections: 已快取的 collections
    - cache_size: 快取索引數量
    - max_size: 最大快取數量
    """
    # 新架構：通過 hybrid_retriever 訪問 bm25_retriever
    stats = retrieval_service.hybrid_retriever.bm25_retriever.get_cache_stats()

    return success_response(
        data=stats,
        message=t('retrieval.statsSuccess')
    )


@router.post(
    "/bm25/invalidate/{collection_id}",
    summary="使 BM25 索引失效",
    description="手動觸發 BM25 索引失效 (通常由系統自動觸發)"
)
async def invalidate_bm25_index(
    collection_id: int,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    手動使 BM25 索引失效

    使用場景:
    - 測試索引更新機制
    - 手動強制重建索引

    注意: 通常由系統在資料變更時自動觸發,無需手動調用
    """
    # 新架構：通過 hybrid_retriever 訪問 bm25_retriever
    await retrieval_service.hybrid_retriever.bm25_retriever.invalidate_collection(collection_id)

    return success_response(
        data={"collection_id": collection_id},
        message=t('retrieval.invalidateSuccess', collection_id=collection_id)
    )