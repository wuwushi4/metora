# -*- coding: utf-8 -*-
"""
Collection 管理相關的 Pydantic Schemas
定義 Collection CRUD 的 API 請求和響應結構
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ===========================================
# Collection CRUD Schemas
# ===========================================

class CollectionCreate(BaseModel):
    """建立 Collection 請求"""
    name: str = Field(..., description="集合名稱", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="集合描述", max_length=500)
    chunking_strategy: str = Field(
        default="qa_multi_representation",
        description="分塊策略名稱",
        max_length=50
    )

    @field_validator('name')
    @classmethod
    def strip_name(cls, v: str) -> str:
        """清除前後空白字符"""
        return v.strip() if v else v

    @field_validator('description')
    @classmethod
    def strip_description(cls, v: Optional[str]) -> Optional[str]:
        """清除描述的前後空白字符"""
        return v.strip() if v else v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "RAG 知識庫",
                    "description": "用於客服問答的知識庫",
                    "chunking_strategy": "qa_multi_representation"
                }
            ]
        }
    }


class CollectionUpdate(BaseModel):
    """更新 Collection 請求（部分更新）"""
    name: Optional[str] = Field(None, description="集合名稱", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="集合描述", max_length=500)

    @field_validator('name')
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        """清除名稱的前後空白字符"""
        return v.strip() if v else v

    @field_validator('description')
    @classmethod
    def strip_description(cls, v: Optional[str]) -> Optional[str]:
        """清除描述的前後空白字符"""
        return v.strip() if v else v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "更新後的集合名稱",
                    "description": "更新後的描述"
                }
            ]
        }
    }


class OwnerInfo(BaseModel):
    """所有者資訊"""
    id: int = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    full_name: Optional[str] = Field(None, description="真實姓名")

    model_config = {"from_attributes": True}


class CollectionResponse(BaseModel):
    """Collection 響應"""
    id: int = Field(..., description="集合ID")
    name: str = Field(..., description="集合名稱")
    description: Optional[str] = Field(None, description="集合描述")
    user_id: int = Field(..., description="所有者ID")
    chunking_strategy: str = Field(..., description="分塊策略名稱")
    dataset_count: int = Field(default=0, description="資料集數量")
    owner: Optional[OwnerInfo] = Field(None, description="所有者資訊")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "RAG 知識庫",
                    "description": "用於客服問答的知識庫",
                    "user_id": 1,
                    "chunking_strategy": "qa_multi_representation",
                    "dataset_count": 5,
                    "created_at": "2025-10-15T10:00:00Z",
                    "updated_at": "2025-10-15T10:00:00Z"
                }
            ]
        }
    }


class CollectionListParams(BaseModel):
    """Collection 列表查詢參數"""
    page: int = Field(default=1, ge=1, description="頁碼（從 1 開始）")
    page_size: int = Field(default=20, ge=1, le=100, description="每頁筆數（1-100）")
    name: Optional[str] = Field(None, description="集合名稱（模糊搜尋）")
    chunking_strategy: Optional[str] = Field(None, description="分塊策略（精確搜尋）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 1,
                    "page_size": 20,
                    "name": "知識庫",
                    "chunking_strategy": "qa_multi_representation"
                }
            ]
        }
    }
