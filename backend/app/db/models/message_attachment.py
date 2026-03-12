# -*- coding: utf-8 -*-
"""
訊息附件模型
"""
from typing import TYPE_CHECKING, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Integer, ForeignKey, Index, JSON, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.chat_message import ChatMessage


class AttachmentType(str, Enum):
    """附件類型"""

    IMAGE = "image"
    PDF_PAGE = "pdf_page"
    # 未來可擴展: AUDIO, VIDEO, DOCUMENT


class MessageAttachment(Base):
    """訊息附件模型"""

    __tablename__ = "message_attachments"

    # 主鍵
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="附件ID",
    )

    # 關聯訊息
    message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        comment="訊息ID",
    )

    # 附件類型
    attachment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="附件類型 (image | pdf_page)",
    )

    # 檔案資訊
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="檔案儲存路徑"
    )

    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="原始檔案名稱"
    )

    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="檔案大小 (bytes)"
    )

    mime_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="MIME 類型"
    )

    # 附加資訊 (圖片尺寸、PDF 頁碼等)
    # 使用 extra_data 與 ChatMessage 保持一致
    extra_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        comment="附件元資料 (尺寸、頁碼、父檔案等)",
    )

    # 處理狀態 (未來可用於非同步處理)
    processing_status: Mapped[str] = mapped_column(
        String(20),
        default="completed",
        nullable=False,
        comment="處理狀態 (pending | processing | completed | failed)",
    )

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="建立時間",
    )

    # 關聯
    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage", back_populates="attachments", lazy="selectin"
    )

    # 索引
    __table_args__ = (
        Index("ix_message_attachments_message_id", "message_id"),
        Index("ix_message_attachments_type", "attachment_type"),
        Index("ix_message_attachments_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<MessageAttachment(id={self.id}, type='{self.attachment_type}', message_id={self.message_id})>"
