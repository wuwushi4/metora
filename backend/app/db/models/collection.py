# -*- coding: utf-8 -*-
"""
Collection 模型 - 資料集合（如：專案A）
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# ==========================================
# TYPE_CHECKING 條件導入
# ==========================================
# 避免循環引用問題：Collection ↔ User, Collection ↔ Dataset
if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.dataset import Dataset


class Collection(Base, TimestampMixin):
    """Collection 模型 - 資料集合"""
    __tablename__ = "collections"

    # 主鍵
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        comment="集合ID"
    )

    # 基本資訊
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="集合名稱"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="集合描述"
    )

    # 所有者
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所有者ID"
    )

    # 分塊策略
    chunking_strategy: Mapped[str] = mapped_column(
        String(50),
        default="qa_multi_representation",
        nullable=False,
        comment="分塊策略名稱"
    )

    # 關聯 - 使用字串避免循環引用
    user: Mapped["User"] = relationship(
        "User",
        back_populates="collections",
        lazy="selectin"  # 自動載入，避免 N+1 問題
    )

    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        back_populates="collection",
        cascade="all, delete-orphan",  # 刪除 Collection 時級聯刪除所有 Dataset
        lazy="selectin"  # 自動載入，避免 N+1 問題
    )

    # 索引
    __table_args__ = (
        Index('ix_collections_user_id', 'user_id'),
        Index('ix_collections_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name='{self.name}', user_id={self.user_id})>"
