# -*- coding: utf-8 -*-
"""
Regulation 模型 - 法規資料
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# ==========================================
# TYPE_CHECKING 條件導入
# ==========================================
# 避免循環引用問題：Regulation ↔ User
if TYPE_CHECKING:
    from app.db.models.user import User


class Regulation(Base, TimestampMixin):
    """Regulation 模型 - 法規資料"""
    __tablename__ = "regulations"

    # 主鍵
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        comment="法規ID"
    )

    # 基本資訊
    law_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="法規代碼（如：D0050001）"
    )
    law_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="法規名稱"
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="其他",
        nullable=False,
        comment="法規類別"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="現行",
        nullable=False,
        comment="法規狀態（現行/廢止等）"
    )
    last_updated: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="最後更新日期（YYYY-MM-DD）"
    )

    # 完整法規內容（JSONB）
    content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="完整法規內容（包含 chapters 和 law_metadata）"
    )

    # 所有者
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所有者ID"
    )

    # 關聯 - 使用字串避免循環引用
    user: Mapped["User"] = relationship(
        "User",
        back_populates="regulations",
        lazy="noload"  # 不自動加載，需要顯式 eager loading
    )

    # 索引
    __table_args__ = (
        Index('ix_regulations_user_id', 'user_id'),
        Index('ix_regulations_law_code', 'law_code'),
        Index('ix_regulations_law_name', 'law_name'),
        Index('ix_regulations_category', 'category'),
        Index('ix_regulations_status', 'status'),
        # GIN 索引支援 JSONB 查詢
        Index(
            'ix_regulations_content_gin',
            'content',
            postgresql_using='gin'
        ),
    )

    def __repr__(self) -> str:
        return f"<Regulation(id={self.id}, law_code='{self.law_code}', law_name='{self.law_name}')>"
