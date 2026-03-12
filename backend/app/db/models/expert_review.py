# -*- coding: utf-8 -*-
"""
專家審查資料模型

用於記錄領域專家對負面反饋的審查意見和建議回覆,
支援後續的 DPO 微調資料準備。
"""
from typing import TYPE_CHECKING, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy import Text, ForeignKey, Index, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.message_feedback import MessageFeedback
    from app.db.models.user import User


class ExpertReview(Base):
    """專家審查表"""
    __tablename__ = "expert_reviews"

    # 主鍵
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="審查記錄 ID"
    )

    # 外鍵關聯
    feedback_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("message_feedbacks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="關聯的反饋 ID (一對一)"
    )
    reviewed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="審查者使用者 ID"
    )

    # 審查內容
    expert_opinion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="專家意見"
    )
    suggested_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="建議回覆內容(用於 DPO 微調)"
    )

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="建立時間"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最後更新時間"
    )

    # 關聯關係
    feedback: Mapped["MessageFeedback"] = relationship(
        "MessageFeedback",
        back_populates="expert_review",
        lazy="selectin"  # 避免 N+1 查詢
    )
    reviewer: Mapped["User"] = relationship(
        "User",
        lazy="selectin"  # 預載入審查者資訊
    )

    # 索引
    __table_args__ = (
        Index("idx_expert_reviews_feedback_id", "feedback_id"),
        Index("idx_expert_reviews_reviewed_by", "reviewed_by"),
        Index("idx_expert_reviews_created_at", "created_at"),
        Index("idx_expert_reviews_reviewer_created", "reviewed_by", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ExpertReview(id={self.id}, feedback_id={self.feedback_id})>"
