# -*- coding: utf-8 -*-
"""
提示詞模組的 Pydantic Schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class PromptTemplateBase(BaseModel):
    """提示詞基礎 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="提示詞名稱")
    content: str = Field(..., min_length=1, max_length=5000, description="提示詞內容")
    description: Optional[str] = Field(None, max_length=500, description="提示詞描述")


class PromptTemplateCreateRequest(PromptTemplateBase):
    """建立提示詞請求"""
    is_favorite: bool = Field(False, description="是否收藏此提示詞")

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """驗證內容長度"""
        if len(v.strip()) == 0:
            raise ValueError("提示詞內容不能為空")
        return v.strip()


class PromptTemplateUpdateRequest(BaseModel):
    """更新提示詞請求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    description: Optional[str] = Field(None, max_length=500)


class PromptTemplateResponse(PromptTemplateBase):
    """提示詞回應"""
    id: UUID
    user_id: int
    is_favorite: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
