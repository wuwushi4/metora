# -*- coding: utf-8 -*-
"""
Dataset 模型 - 資料集（如：會議紀錄.txt）
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Integer, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# ==========================================
# TYPE_CHECKING 條件導入
# ==========================================
# 避免循環引用問題：Dataset ↔ Collection
if TYPE_CHECKING:
    from app.db.models.collection import Collection


class Dataset(Base, TimestampMixin):
    """Dataset 模型 - 資料集"""
    __tablename__ = "datasets"

    # 主鍵
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        comment="資料集ID"
    )

    # 所屬集合
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        comment="所屬集合ID"
    )

    # 檔案資訊
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="儲存檔名（UUID）"
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始檔名"
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="檔案完整路徑"
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="檔案大小（bytes）"
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="檔案類型（副檔名）"
    )

    # 向量化資訊
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="分塊數量"
    )
    vectorized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已向量化"
    )
    vectorization_error: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="向量化錯誤訊息"
    )

    # 關聯 - 使用字串避免循環引用
    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="datasets",
        lazy="selectin"  # 自動載入，避免 N+1 問題
    )

    # 索引
    __table_args__ = (
        Index('ix_datasets_collection_id', 'collection_id'),
        Index('ix_datasets_vectorized', 'vectorized'),
        Index('ix_datasets_filename', 'filename'),
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, filename='{self.filename}', collection_id={self.collection_id})>"
