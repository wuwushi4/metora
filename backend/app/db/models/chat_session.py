# -*- coding: utf-8 -*-
"""
聊天 Session 模型
"""
from typing import TYPE_CHECKING, List
from uuid import uuid4

from sqlalchemy import String, Boolean, Integer, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.chat_message import ChatMessage


class ChatSession(Base, TimestampMixin):
    """聊天 Session 模型"""
    __tablename__ = "chat_sessions"

    # 主鍵
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Session ID"
    )

    # 關聯使用者
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="使用者ID"
    )

    # Session 資訊
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="對話標題"
    )
    graph_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Graph 類型 (base_graph | rag_graph | deep_research)"
    )
    collection_ids: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        comment="選擇的 Collection IDs"
    )

    # 狀態
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否啟用"
    )

    # 關聯
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_sessions",
        lazy="selectin"
    )

    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",  # 刪除 Session 時級聯刪除所有訊息
        lazy="selectin",
        order_by="ChatMessage.created_at"  # 按時間排序
    )

    # 索引
    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
        Index("ix_chat_sessions_is_active", "is_active"),
        Index("ix_chat_sessions_user_active", "user_id", "is_active"),  # 複合索引
        Index("ix_chat_sessions_created_at", "created_at"),  # 用於全局時間範圍統計查詢 (Dashboard)
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title='{self.title}', graph_type='{self.graph_type}')>"
