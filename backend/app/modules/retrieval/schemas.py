# -*- coding: utf-8 -*-
"""
Retrieval 管理相關的 Pydantic Schemas
定義 Retrieval 的 API 請求和響應結構
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Document:
    """
    檢索結果文檔（內部使用）

    用於檢索器之間傳遞結果，與 Pydantic 的 DocumentResponse 區分。
    這是一個簡單的數據類別，不需要 Pydantic 的驗證開銷。
    """

    def __init__(
        self,
        id: str,
        content: str,
        metadata: dict,
        score: float = 0.0
    ):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.score = score

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score
        }


class DocumentResponse(BaseModel):
    """文檔響應模型"""
    id: str = Field(..., description="文檔 ID")
    content: str = Field(..., description="文檔內容")
    score: float = Field(
        ...,
        description=(
            "相關性分數,範圍 [0, 1],值越大越相關。\n"
            "- 使用 BGE Reranker 時: Sigmoid(logits),表示語義相關機率\n"
            "- 未使用 Reranker 時: Sigmoid(RRF分數),表示排名融合後的相關性\n"
            "可直接視為百分比 (0% = 不相關, 100% = 極度相關)。\n"
            "原始分數保留在 metadata['reranker_logits'] 或 metadata['rrf_score'] 中。"
        )
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "c1_d1_qa1_question",
                "content": "什麼是機器學習?",
                "score": 0.85,
                "metadata": {
                    "collection_id": 1,
                    "dataset_id": 1,
                    "qa_id": "qa1",
                    "representation": "question"
                }
            }
        }


class SearchRequest(BaseModel):
    """檢索請求模型"""
    query: str = Field(..., description="查詢文本", min_length=1)
    collection_ids: List[int] = Field(..., description="目標 Collection IDs", min_length=1)
    top_k: int = Field(default=3, description="返回結果數量", ge=1, le=20)
    enable_rerank: bool = Field(default=True, description="是否啟用 BGE 重排序")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "機器學習的基本概念",
                "collection_ids": [1, 2],
                "top_k": 5,
                "enable_rerank": True
            }
        }


class SearchResult(BaseModel):
    """檢索結果模型"""
    query: str = Field(..., description="查詢文本")
    results: List[DocumentResponse] = Field(..., description="檢索結果")
    total: int = Field(..., description="結果總數")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "機器學習的基本概念",
                "results": [
                    {
                        "id": "c1_d1_qa1_question",
                        "content": "什麼是機器學習?",
                        "score": 0.85,
                        "metadata": {}
                    }
                ],
                "total": 1
            }
        }


class RAGRequest(BaseModel):
    """RAG 查詢請求模型"""
    query: str = Field(..., description="使用者查詢", min_length=1)
    collection_ids: List[int] = Field(..., description="目標 Collection IDs", min_length=1)
    enable_query_decomposition: bool = Field(default=False, description="是否啟用查詢重構")
    top_k: int = Field(default=3, description="每個子查詢返回結果數量", ge=1, le=10)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "請說明深度學習的應用領域",
                "collection_ids": [1],
                "enable_query_decomposition": False,
                "top_k": 3
            }
        }


class RAGResponse(BaseModel):
    """RAG 查詢響應模型"""
    query: str = Field(..., description="原始查詢")
    sub_queries: List[str] = Field(..., description="子查詢列表")
    retrieved_docs: List[DocumentResponse] = Field(..., description="檢索到的文檔")
    answer: str = Field(..., description="生成的回答")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "請說明深度學習的應用領域",
                "sub_queries": ["請說明深度學習的應用領域"],
                "retrieved_docs": [
                    {
                        "id": "c1_d1_qa1_answer",
                        "content": "深度學習廣泛應用於圖像識別、自然語言處理、語音識別等領域。",
                        "score": 0.92,
                        "metadata": {}
                    }
                ],
                "answer": "深度學習是機器學習的一個分支,主要應用領域包括:..."
            }
        }
