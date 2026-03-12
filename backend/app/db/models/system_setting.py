# -*- coding: utf-8 -*-
"""
系統設定模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class SystemSetting(Base, TimestampMixin):
    """系統設定模型"""
    __tablename__ = "system_settings"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="設定 ID")

    # 設定資訊
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="設定分類 (auth, rag, chat, upload)"
    )
    setting_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="設定鍵"
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="設定值 (JSON 格式儲存)"
    )
    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="值類型 (int, float, bool, string, array)"
    )
    default_value: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="預設值"
    )

    # 顯示資訊
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="顯示名稱 (繁體中文)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="說明"
    )

    # 驗證規則
    min_value: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="最小值 (數值型態)"
    )
    max_value: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="最大值 (數值型態)"
    )
    validation_rules: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment="驗證規則 (JSON 格式)"
    )

    # 狀態
    requires_restart: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否需要重啟"
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否敏感 (不在前端顯示)"
    )

    # 修改資訊
    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="修改者 ID"
    )

    # 關聯 - 修改者
    updater: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[updated_by],
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SystemSetting(id={self.id}, key='{self.setting_key}', value='{self.value}')>"


class SystemSettingAudit(Base):
    """系統設定審計日誌模型"""
    __tablename__ = "system_settings_audit"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="審計日誌 ID")

    # 設定資訊
    setting_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="設定鍵"
    )
    old_value: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="舊值"
    )
    new_value: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="新值"
    )

    # 修改資訊
    changed_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="修改者 ID"
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="修改時間"
    )
    change_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="修改原因"
    )

    # 關聯 - 修改者
    changer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[changed_by],
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SystemSettingAudit(id={self.id}, key='{self.setting_key}', changed_at='{self.changed_at}')>"
