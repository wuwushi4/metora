# -*- coding: utf-8 -*-
"""
Dataset 管理相關的 Pydantic Schemas
定義 Dataset CRUD 的 API 請求和響應結構
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ===========================================
# Dataset CRUD Schemas
# ===========================================

class DatasetResponse(BaseModel):
    """Dataset 響應"""
    id: int = Field(..., description="資料集ID")
    collection_id: int = Field(..., description="所屬集合ID")
    filename: str = Field(..., description="儲存檔名（UUID）")
    original_filename: str = Field(..., description="原始檔名")
    file_path: str = Field(..., description="檔案完整路徑")
    file_size: int = Field(..., description="檔案大小（bytes）")
    file_type: str = Field(..., description="檔案類型（副檔名）")
    chunk_count: int = Field(..., description="分塊數量")
    vectorized: bool = Field(..., description="是否已向量化")
    vectorization_error: Optional[str] = Field(None, description="向量化錯誤訊息")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "collection_id": 1,
                    "filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.json",
                    "original_filename": "qa_data.json",
                    "file_path": "uploads/2025/10/a1b2c3d4-e5f6-7890-abcd-ef1234567890.json",
                    "file_size": 102400,
                    "file_type": ".json",
                    "chunk_count": 10,
                    "vectorized": True,
                    "vectorization_error": None,
                    "created_at": "2025-10-15T10:00:00Z",
                    "updated_at": "2025-10-15T10:05:00Z"
                }
            ]
        }
    }


class DatasetListParams(BaseModel):
    """Dataset 列表查詢參數"""
    page: int = Field(default=1, ge=1, description="頁碼（從 1 開始）")
    page_size: int = Field(default=20, ge=1, le=100, description="每頁筆數（1-100）")
    collection_id: Optional[int] = Field(None, description="所屬集合ID（精確搜尋）")
    vectorized: Optional[bool] = Field(None, description="是否已向量化（精確搜尋）")
    original_filename: Optional[str] = Field(None, description="原始檔名（模糊搜尋）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 1,
                    "page_size": 20,
                    "collection_id": 1,
                    "vectorized": True,
                    "original_filename": "qa_data"
                }
            ]
        }
    }


class ChunkingDefaultsResponse(BaseModel):
    """遞迴分塊預設參數回應"""
    chunk_size: int = Field(..., description="分塊大小（字元數）")
    chunk_overlap: int = Field(..., description="重疊大小（字元數）")

    model_config = {
        "json_schema_extra": {
            "examples": [{"chunk_size": 1000, "chunk_overlap": 200}]
        }
    }


class UploadResponse(BaseModel):
    """檔案上傳響應"""
    dataset: DatasetResponse = Field(..., description="Dataset 資訊")
    message: str = Field(..., description="提示訊息")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dataset": {
                        "id": 1,
                        "collection_id": 1,
                        "filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.json",
                        "original_filename": "qa_data.json",
                        "file_path": "uploads/2025/10/a1b2c3d4-e5f6-7890-abcd-ef1234567890.json",
                        "file_size": 102400,
                        "file_type": ".json",
                        "chunk_count": 0,
                        "vectorized": False,
                        "vectorization_error": None,
                        "created_at": "2025-10-15T10:00:00Z",
                        "updated_at": "2025-10-15T10:00:00Z"
                    },
                    "message": "檔案上傳成功，向量化處理中..."
                }
            ]
        }
    }
