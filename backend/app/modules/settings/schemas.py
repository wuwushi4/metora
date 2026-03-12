# -*- coding: utf-8 -*-
"""
系統設定相關的 Pydantic Schemas
定義設定管理的 API 請求和響應結構
"""
from typing import Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# ===========================================
# 設定 Response Schemas
# ===========================================

class SettingResponse(BaseModel):
    """單一設定回應 (對應資料庫模型)"""
    id: int = Field(..., description="設定 ID")
    category: str = Field(..., description="設定分類")
    setting_key: str = Field(..., description="設定鍵")
    value: Any = Field(..., description="設定值(已轉換為對應類型)")
    value_type: str = Field(..., description="值類型")
    default_value: Optional[Any] = Field(None, description="預設值")
    display_name: str = Field(..., description="顯示名稱")
    description: Optional[str] = Field(None, description="說明")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    requires_restart: bool = Field(default=False, description="是否需要重啟")
    is_sensitive: bool = Field(default=False, description="是否敏感")
    updated_at: Optional[datetime] = Field(None, description="更新時間")
    updated_by: Optional[int] = Field(None, description="更新者 ID")

    model_config = {
        "from_attributes": True,  # 允許從 ORM 模型轉換
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "category": "rag",
                "setting_key": "RAG_RETRIEVER_TOP_K",
                "value": 3,
                "value_type": "int",
                "display_name": "檢索結果數量 (Top-K)",
                "min_value": 1,
                "max_value": 20,
                "requires_restart": False
            }]
        }
    }


class SettingsGroupResponse(BaseModel):
    """設定分組回應 (按分類組織)"""
    auth: List[SettingResponse] = Field(default_factory=list, description="認證設定")
    rag: List[SettingResponse] = Field(default_factory=list, description="RAG 設定")
    chat: List[SettingResponse] = Field(default_factory=list, description="對話設定")
    upload: List[SettingResponse] = Field(default_factory=list, description="上傳設定")


# ===========================================
# 設定 Update Schemas
# ===========================================

class SettingUpdate(BaseModel):
    """更新單一設定請求"""
    value: Any = Field(..., description="新的設定值")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        """基本驗證 (詳細驗證在 service 層)"""
        if v is None:
            raise ValueError('設定值不能為 None')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "value": 5
            }]
        }
    }


class SettingsBatchUpdate(BaseModel):
    """批量更新設定請求"""
    settings: List[dict] = Field(
        ...,
        description="設定列表",
        min_length=1,
        examples=[[
            {"key": "RAG_RETRIEVER_TOP_K", "value": 5},
            {"key": "VECTOR_SEARCH_SCORE_THRESHOLD", "value": 0.7}
        ]]
    )

    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v):
        """驗證設定格式"""
        for setting in v:
            if 'key' not in setting or 'value' not in setting:
                raise ValueError('每個設定必須包含 key 和 value 欄位')
        return v


# ===========================================
# 設定 Query Params
# ===========================================

class SettingListParams(BaseModel):
    """設定列表查詢參數 (可選)"""
    category: Optional[str] = Field(None, description="篩選分類")
    search: Optional[str] = Field(None, description="搜尋關鍵字")
