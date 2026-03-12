# -*- coding: utf-8 -*-
"""
Chat 模組的資料模型定義
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from uuid import UUID


# ==================== Session ====================

class SessionCreateRequest(BaseModel):
    """建立 Session 請求"""
    title: Optional[str] = Field(None, max_length=255, description="對話標題（可選，不提供則自動生成）")
    graph_type: Literal["base_graph", "rag_graph", "regulation_graph", "agent_graph"] = Field(..., description="Graph 類型")
    collection_ids: List[int] = Field(default_factory=list, description="Collection IDs")

    @validator("collection_ids")
    def validate_collections(cls, v, values):
        """驗證：base_graph/agent_graph 不能選擇 Collections；rag_graph 和 regulation_graph 必須選擇至少一個 Collection"""
        graph_type = values.get("graph_type")

        if graph_type in ["base_graph", "agent_graph"] and len(v) > 0:
            raise ValueError(f"{graph_type} 不支援選擇 Collections")

        if graph_type in ["rag_graph", "regulation_graph"] and len(v) == 0:
            raise ValueError(f"{graph_type} 必須選擇至少一個 Collection")

        return v


class SessionUpdateRequest(BaseModel):
    """更新 Session 請求"""
    title: Optional[str] = Field(None, max_length=255, description="對話標題")


class SessionResponse(BaseModel):
    """Session 回應"""
    id: UUID
    user_id: int
    title: str
    graph_type: str
    collection_ids: List[int]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: Optional[int] = None  # 訊息數量（可選）

    # 搜尋相關欄位（僅在搜尋 API 使用）
    match_count: Optional[int] = Field(None, description="匹配的訊息數量")
    matched_snippets: Optional[List[str]] = Field(None, description="匹配的訊息片段（最多2條）")
    highlight_keyword: Optional[str] = Field(None, description="搜尋關鍵字")

    class Config:
        from_attributes = True


# ==================== Message ====================

class MessageSendRequest(BaseModel):
    """發送訊息請求"""
    content: str = Field(..., min_length=1, max_length=10000, description="訊息內容")


class PartialMessageCreate(BaseModel):
    """保存部分訊息請求（用於中斷情境）"""
    content: str = Field(..., min_length=1, max_length=50000, description="部分訊息內容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元資料")


class MessageAttachmentResponse(BaseModel):
    """訊息附件回應"""
    id: UUID
    message_id: UUID
    attachment_type: str
    file_path: str
    original_filename: str
    file_size: int
    mime_type: str
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """訊息回應"""
    id: UUID
    session_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="元資料（檢索結果、處理時間等）",
        validation_alias="extra_data"  # 從資料庫的 extra_data 欄位讀取（僅用於輸入）
    )
    created_at: datetime
    attachments: Optional[List[MessageAttachmentResponse]] = Field(
        None,
        description="附件列表（圖片、PDF 等）"
    )
    user_feedback: Optional[Dict[str, Any]] = Field(
        None,
        description="使用者對此訊息的反饋（僅助手訊息有效）"
    )

    class Config:
        from_attributes = True
        populate_by_name = True  # 允許使用 extra_data 或 metadata 兩種名稱


class MessageChunk(BaseModel):
    """串流訊息片段"""
    type: Literal["user_message", "node_start", "node_end", "metadata", "token", "tool_call", "tool_result", "done", "error"]
    node: Optional[str] = None          # 節點名稱（type=node_start/node_end 時）
    step: Optional[str] = None          # 步驟名稱（type=metadata 時）
    content: Optional[str] = None       # 文本內容（type=token/error 時）
    data: Optional[Dict[str, Any]] = None  # 元資料（type=metadata/done/user_message 時）
    message: Optional[MessageResponse] = None  # 完整訊息（type=user_message 時）


# ==================== Graph ====================

class GraphInfo(BaseModel):
    """Graph 資訊"""
    name: str
    description: str
    supports_collections: bool
