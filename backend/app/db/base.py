# -*- coding: utf-8 -*-
"""
SQLAlchemy Base 類別定義
所有 ORM 模型都應繼承此 Base
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TimestampMixin:
    """
    時間戳記 Mixin
    提供 created_at 和 updated_at 欄位
    """

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
        comment="更新時間"
    )


class Base(DeclarativeBase):
    """ORM 模型基礎類別"""
    pass
