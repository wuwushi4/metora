# -*- coding: utf-8 -*-
"""
系統提示詞模板模型
"""
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PromptTemplate(Base, TimestampMixin):
    """系統提示詞模板表"""
    __tablename__ = "prompt_templates"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="主鍵"
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="使用者 ID"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="提示詞名稱"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="提示詞內容（最多 5000 字）"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="提示詞描述"
    )
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否收藏此提示詞"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否啟用（軟刪除）"
    )

    # 關聯
    user = relationship("User", back_populates="prompt_templates")

    def __repr__(self) -> str:
        return f"<PromptTemplate(id={self.id}, name={self.name}, user_id={self.user_id})>"
