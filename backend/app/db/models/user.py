# -*- coding: utf-8 -*-
"""
使用者模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Boolean, DateTime, Table, Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# ==========================================
# TYPE_CHECKING 條件導入
# ==========================================
# 說明：
# 1. TYPE_CHECKING 是 typing 模組提供的常數，在類型檢查時為 True，執行時為 False
# 2. 在此區塊內導入的類型只在類型檢查時存在，執行時不會真正導入
# 3. 這樣可以避免循環引用問題（User 和 Role 互相引用）
# 4. 同時讓類型檢查器（如 Pylance, mypy, basedpyright）能正確識別類型
#
# 使用時機：
# - 當兩個模型之間有雙向關聯（如 User ↔ Role）
# - 需要在類型提示中引用對方的類型
# - 但直接導入會造成循環引用
#
# 最佳實踐：
# - 在 TYPE_CHECKING 區塊內導入類型
# - 在 relationship() 的類型提示中使用字串形式（如 "Role"）
# - 這是 SQLAlchemy + Python 類型提示的標準做法
# ==========================================
if TYPE_CHECKING:
    from app.db.models.role import Role
    from app.db.models.collection import Collection
    from app.db.models.chat_session import ChatSession
    from app.db.models.message_feedback import MessageFeedback
    from app.db.models.regulation import Regulation
    from app.db.models.prompt_template import PromptTemplate

# 使用者-角色關聯表 (多對多)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base, TimestampMixin):
    """使用者模型"""
    __tablename__ = "users"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="使用者ID")

    # 基本資訊
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="使用者名稱"
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="電子郵件"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="加密後的密碼"
    )

    # 個人資訊
    full_name: Mapped[Optional[str]] = mapped_column(String(100), comment="真實姓名")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), comment="頭像URL")

    # 狀態
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="帳號是否啟用"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否為超級管理員"
    )

    # 時間戳記
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="最後登入時間"
    )

    # 關聯 - 使用字串避免循環引用
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"  # 自動載入,避免 N+1 問題
    )

    collections: Mapped[List["Collection"]] = relationship(
        "Collection",
        back_populates="user",
        cascade="all, delete-orphan",  # 刪除使用者時級聯刪除所有 Collection
        lazy="selectin"  # 自動載入,避免 N+1 問題
    )

    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",  # 刪除使用者時級聯刪除所有 ChatSession
        lazy="selectin"
    )

    message_feedbacks: Mapped[List["MessageFeedback"]] = relationship(
        "MessageFeedback",
        back_populates="user",
        cascade="all, delete-orphan",  # 刪除使用者時級聯刪除所有反饋
        lazy="selectin"
    )

    regulations: Mapped[List["Regulation"]] = relationship(
        "Regulation",
        back_populates="user",
        cascade="all, delete-orphan",  # 刪除使用者時級聯刪除所有法規
        lazy="noload"  # 預設不載入，避免每次查詢 User 都載入所有法規
    )

    prompt_templates: Mapped[List["PromptTemplate"]] = relationship(
        "PromptTemplate",
        back_populates="user",
        cascade="all, delete-orphan",  # 刪除使用者時級聯刪除所有提示詞模板
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
