# -*- coding: utf-8 -*-
"""
Refresh Token 模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ==========================================
# TYPE_CHECKING 條件導入
# ==========================================
# 說明：
# 1. TYPE_CHECKING 是 typing 模組提供的常數，在類型檢查時為 True，執行時為 False
# 2. 在此區塊內導入的類型只在類型檢查時存在，執行時不會真正導入
# 3. 這樣可以避免循環引用問題（RefreshToken 引用 User）
# 4. 同時讓類型檢查器（如 Pylance, mypy, basedpyright）能正確識別類型
#
# 使用時機：
# - 當模型之間有關聯（如 RefreshToken → User）
# - 需要在類型提示中引用其他模型的類型
# - 為了保持一致性和避免潛在的循環引用
#
# 最佳實踐：
# - 在 TYPE_CHECKING 區塊內導入類型
# - 在 relationship() 的類型提示中使用字串形式（如 "User"）
# - 這是 SQLAlchemy + Python 類型提示的標準做法
# ==========================================
if TYPE_CHECKING:
    from app.db.models.user import User


class RefreshToken(Base):
    """Refresh Token 模型"""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="Token ID")

    token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        nullable=False,
        comment="Refresh Token"
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="使用者ID"
    )

    # Token 資訊
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="過期時間"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="建立時間"
    )

    # 裝置資訊(可選)
    device_info: Mapped[Optional[str]] = mapped_column(String(200), comment="裝置資訊")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), comment="IP位址")

    # 關聯
    user: Mapped["User"] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return f"<RefreshToken(user_id={self.user_id}, expires_at={self.expires_at})>"
