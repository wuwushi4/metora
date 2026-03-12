# -*- coding: utf-8 -*-
"""
角色模型
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

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
# - 在 relationship() 的類型提示中使用字串形式（如 "User"）
# - 這是 SQLAlchemy + Python 類型提示的標準做法
# ==========================================
if TYPE_CHECKING:
    from app.db.models.user import User


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="角色ID")
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="角色名稱"
    )
    description: Mapped[Optional[str]] = mapped_column(String(200), comment="角色描述")

    # 權限列表(JSON 格式儲存)
    permissions: Mapped[Optional[str]] = mapped_column(
        String(1000),
        comment="權限列表(JSON格式)"
    )

    # 關聯 - 需要 import User 和 user_roles,但為避免循環引用,使用字串
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",  # 使用字串避免循環引用
        back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
