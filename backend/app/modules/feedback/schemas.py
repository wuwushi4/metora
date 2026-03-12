# -*- coding: utf-8 -*-
"""
訊息反饋 Pydantic 模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.db.models.message_feedback import FeedbackType


# ==========================================
# 基礎模型
# ==========================================

class UserBasicInfo(BaseModel):
    """使用者基本資訊"""
    id: int = Field(..., description="使用者 ID")
    username: str = Field(..., description="使用者名稱")
    full_name: Optional[str] = Field(None, description="真實姓名")

    class Config:
        from_attributes = True


class AttachmentInfo(BaseModel):
    """附件資訊"""
    id: UUID = Field(..., description="附件 ID")
    attachment_type: str = Field(..., description="附件類型 (image | pdf_page)")
    original_filename: str = Field(..., description="原始檔案名稱")
    file_size: int = Field(..., description="檔案大小 (bytes)")
    mime_type: str = Field(..., description="MIME 類型")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="附件元資料")

    class Config:
        from_attributes = True


class MessageWithMetadata(BaseModel):
    """訊息與元資料"""
    id: UUID = Field(..., description="訊息 ID")
    role: str = Field(..., description="角色 (user | assistant | system)")
    content: str = Field(..., description="訊息內容")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="元資料(包含 RAG 檢索結果等)")
    created_at: datetime = Field(..., description="建立時間")
    attachments: List[AttachmentInfo] = Field(default_factory=list, description="訊息附件")

    class Config:
        from_attributes = True


# ==========================================
# 請求模型 (Request)
# ==========================================

class FeedbackCreate(BaseModel):
    """建立反饋請求"""
    message_id: UUID = Field(..., description="訊息 ID")
    feedback_type: FeedbackType = Field(..., description="反饋類型: thumbs_up 或 thumbs_down")
    issue_tags: Optional[List[str]] = Field(
        None,
        description="問題標籤列表",
        example=["回答不準確", "內容太簡短"]
    )
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="使用者自由填寫的評論"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "feedback_type": "thumbs_down",
                "issue_tags": ["回答不準確", "檢索結果不相關"],
                "comment": "提供的範例代碼有語法錯誤"
            }
        }


class FeedbackUpdate(BaseModel):
    """更新反饋請求"""
    feedback_type: Optional[FeedbackType] = Field(None, description="反饋類型")
    issue_tags: Optional[List[str]] = Field(None, description="問題標籤列表")
    comment: Optional[str] = Field(None, max_length=2000, description="使用者評論")

    class Config:
        json_schema_extra = {
            "example": {
                "feedback_type": "thumbs_up",
                "issue_tags": None,
                "comment": "更新後覺得回答很好"
            }
        }


# ==========================================
# 回應模型 (Response)
# ==========================================

class FeedbackResponse(BaseModel):
    """反饋回應模型"""
    id: UUID = Field(..., description="反饋 ID")
    message_id: UUID = Field(..., description="訊息 ID")
    user_id: int = Field(..., description="使用者 ID")
    feedback_type: FeedbackType = Field(..., description="反饋類型")
    issue_tags: Optional[List[str]] = Field(None, description="問題標籤列表")
    comment: Optional[str] = Field(None, description="使用者評論")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="最後更新時間")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                "user_id": 1,
                "feedback_type": "thumbs_down",
                "issue_tags": ["回答不準確", "檢索結果不相關"],
                "comment": "提供的範例代碼有語法錯誤",
                "created_at": "2025-10-28T03:30:00Z",
                "updated_at": "2025-10-28T03:30:00Z"
            }
        }


class FeedbackListResponse(BaseModel):
    """反饋列表回應"""
    feedbacks: List[FeedbackResponse] = Field(..., description="反饋列表")
    total: int = Field(..., description="總數")

    class Config:
        json_schema_extra = {
            "example": {
                "feedbacks": [
                    {
                        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "message_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                        "user_id": 1,
                        "feedback_type": "thumbs_up",
                        "issue_tags": None,
                        "comment": None,
                        "created_at": "2025-10-28T03:30:00Z",
                        "updated_at": "2025-10-28T03:30:00Z"
                    }
                ],
                "total": 1
            }
        }


class IssueTagsResponse(BaseModel):
    """問題標籤列表回應"""
    tags: List[str] = Field(..., description="可用的問題標籤列表")

    class Config:
        json_schema_extra = {
            "example": {
                "tags": [
                    "回答不準確",
                    "內容太簡短",
                    "格式錯誤",
                    "檢索結果不相關",
                    "語氣不恰當"
                ]
            }
        }


# ==========================================
# 專家審查相關 (Expert Review)
# ==========================================

class ExpertReviewRequest(BaseModel):
    """提交專家審查請求"""
    expert_opinion: str = Field(..., min_length=10, max_length=5000, description="專家意見")
    suggested_response: Optional[str] = Field(None, max_length=10000, description="建議回覆內容(用於 DPO 微調)")

    class Config:
        json_schema_extra = {
            "example": {
                "expert_opinion": "此回答引用的文件片段不相關,應該使用 dataset_123 中的內容",
                "suggested_response": "根據您的問題,建議回答如下..."
            }
        }


class ExpertReviewResponse(BaseModel):
    """專家審查回應"""
    id: UUID = Field(..., description="審查記錄 ID")
    feedback_id: UUID = Field(..., description="關聯的反饋 ID")
    expert_opinion: str = Field(..., description="專家意見")
    suggested_response: Optional[str] = Field(None, description="建議回覆內容")
    reviewed_by: int = Field(..., description="審查者 ID")
    reviewer: Optional[UserBasicInfo] = Field(None, description="審查者資訊")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="最後更新時間")

    class Config:
        from_attributes = True


class FeedbackDetailResponse(BaseModel):
    """反饋詳情回應"""
    id: UUID = Field(..., description="反饋 ID")
    message_id: UUID = Field(..., description="訊息 ID")
    user_id: int = Field(..., description="使用者 ID")
    user: Optional[UserBasicInfo] = Field(None, description="使用者資訊")
    feedback_type: FeedbackType = Field(..., description="反饋類型")
    issue_tags: Optional[List[str]] = Field(None, description="問題標籤")
    comment: Optional[str] = Field(None, description="使用者評論")
    created_at: datetime = Field(..., description="反饋時間")

    # 關聯資料
    message: MessageWithMetadata = Field(..., description="AI 回覆訊息")
    user_question: Optional[str] = Field(None, description="使用者提問文字(向後相容)")
    user_message: Optional[MessageWithMetadata] = Field(None, description="完整使用者訊息(包含附件)")
    expert_review: Optional[ExpertReviewResponse] = Field(None, description="專家審查")

    # 新增欄位
    graph_type: str = Field(..., description="Agent 類型 (base_graph | rag_graph | regulation_graph)")
    collection_ids: List[int] = Field(default_factory=list, description="知識庫 ID 列表")
    collection_names: List[str] = Field(default_factory=list, description="知識庫名稱列表")

    class Config:
        from_attributes = True


class FeedbackListItem(BaseModel):
    """反饋列表項目"""
    id: UUID = Field(..., description="反饋 ID")
    message_id: UUID = Field(..., description="訊息 ID")
    user: UserBasicInfo = Field(..., description="使用者資訊")
    message_preview: str = Field(..., description="訊息預覽 (前 100 字)")
    feedback_type: FeedbackType = Field(..., description="反饋類型")
    issue_tags: Optional[List[str]] = Field(None, description="問題標籤")
    is_reviewed: bool = Field(..., description="是否已審查")
    is_interrupted: bool = Field(default=False, description="訊息是否為使用者中斷")
    created_at: datetime = Field(..., description="反饋時間")
    # 新增欄位
    graph_type: str = Field(..., description="Agent 類型 (base_graph | rag_graph | regulation_graph)")
    collection_ids: List[int] = Field(default_factory=list, description="知識庫 ID 列表")
    collection_names: List[str] = Field(default_factory=list, description="知識庫名稱列表")

    class Config:
        from_attributes = True


class FeedbackListParams(BaseModel):
    """反饋列表查詢參數"""
    page: int = Field(default=1, ge=1, description="頁碼 (從 1 開始)")
    page_size: int = Field(default=20, ge=1, le=100, description="每頁筆數 (1-100)")
    feedback_type: Optional[FeedbackType] = Field(None, description="反饋類型篩選")
    is_reviewed: Optional[bool] = Field(None, description="是否已審查篩選")
    start_date: Optional[datetime] = Field(None, description="開始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")
    # 新增篩選參數
    graph_type: Optional[str] = Field(None, description="Agent 類型篩選 (base_graph | rag_graph | regulation_graph)")
    collection_id: Optional[int] = Field(None, description="知識庫 ID 篩選 (單選)")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "feedback_type": "thumbs_down",
                "is_reviewed": False,
                "graph_type": "rag_graph",
                "collection_id": 1
            }
        }
