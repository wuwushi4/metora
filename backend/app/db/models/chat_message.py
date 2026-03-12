# -*- coding: utf-8 -*-
"""
聊天訊息模型
"""
from typing import TYPE_CHECKING, Dict, Any
from uuid import uuid4
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Index, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_session import ChatSession
    from app.db.models.message_feedback import MessageFeedback
    from app.db.models.message_attachment import MessageAttachment


class ChatMessage(Base):
    """聊天訊息模型"""
    __tablename__ = "chat_messages"

    # 主鍵
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="訊息ID"
    )

    # 關聯 Session
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Session ID"
    )

    # 訊息內容
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="角色 (user | assistant | system)"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="訊息內容"
    )

    # 元資料（儲存檢索結果、中間節點資訊等）
    # 注意：使用 extra_data 而非 metadata（metadata 是 SQLAlchemy 保留字）
    extra_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="元資料 (檢索結果、處理時間等)"
    )

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="建立時間"
    )

    # 關聯
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
        lazy="selectin"
    )

    feedbacks: Mapped[list["MessageFeedback"]] = relationship(
        "MessageFeedback",
        back_populates="message",
        cascade="all, delete-orphan",  # 刪除訊息時級聯刪除反饋
        lazy="selectin"
    )

    attachments: Mapped[list["MessageAttachment"]] = relationship(
        "MessageAttachment",
        back_populates="message",
        cascade="all, delete-orphan",  # 刪除訊息時級聯刪除附件
        lazy="selectin"
    )

    # 索引
    __table_args__ = (
        # 複合索引：用於查詢特定 session 的訊息並按時間排序
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
        # 單列索引：用於全局時間範圍統計查詢 (Dashboard)
        Index("ix_chat_messages_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>"
