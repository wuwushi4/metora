"""
訊息反饋資料模型

用於記錄使用者對 AI 助理回應的反饋(讚/踩),
用於後續 RAG 召回率分析和 DPO 微調資料準備。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, UniqueConstraint, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.expert_review import ExpertReview


class FeedbackType(str, enum.Enum):
    """反饋類型枚舉"""
    THUMBS_UP = "thumbs_up"      # 讚
    THUMBS_DOWN = "thumbs_down"  # 踩


class MessageFeedback(Base):
    """訊息反饋表"""
    __tablename__ = "message_feedbacks"

    # 主鍵
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # 外鍵關聯
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        comment="關聯的訊息 ID"
    )
    user_id = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="提交反饋的使用者 ID"
    )

    # 反饋內容
    feedback_type = Column(
        SQLEnum(FeedbackType, name="feedback_type_enum", create_type=True),
        nullable=False,
        comment="反饋類型: thumbs_up 或 thumbs_down"
    )
    issue_tags = Column(
        JSON,
        nullable=True,
        comment="問題標籤列表,如 ['回答不準確', '內容太簡短']"
    )
    comment = Column(
        Text,
        nullable=True,
        comment="使用者自由填寫的評論"
    )

    # 時間戳
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="反饋建立時間"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="反饋最後更新時間"
    )

    # 關聯關係
    message = relationship("ChatMessage", back_populates="feedbacks")
    user = relationship("User", back_populates="message_feedbacks")
    expert_review = relationship(
        "ExpertReview",
        back_populates="feedback",
        uselist=False,  # 一對一關聯
        lazy="selectin"  # 預載入審查記錄
    )

    # 約束與索引
    __table_args__ = (
        # 唯一約束: 一個使用者對同一訊息只能有一筆反饋
        UniqueConstraint("message_id", "user_id", name="uq_message_user_feedback"),
        # 複合索引: 用於查詢訊息的反饋
        Index("idx_feedback_message_user", "message_id", "user_id"),
        # 單欄位索引: 用於統計分析
        Index("idx_feedback_type", "feedback_type"),
        Index("idx_feedback_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<MessageFeedback(id={self.id}, message_id={self.message_id}, type={self.feedback_type})>"
