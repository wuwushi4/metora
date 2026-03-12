# -*- coding: utf-8 -*-
"""Add recursive text chunking settings to system_settings

Revision ID: c8e2f1a3b5d7
Revises: b7f8e9d0a1c2
Create Date: 2026-02-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8e2f1a3b5d7'
down_revision: Union[str, Sequence[str], None] = 'b7f8e9d0a1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert recursive text chunking settings into system_settings."""
    op.execute("""
        INSERT INTO system_settings
            (category, setting_key, value, value_type, default_value,
             display_name, description, min_value, max_value, requires_restart)
        VALUES
            ('rag', 'RECURSIVE_TEXT_CHUNK_SIZE', '1000', 'int', '1000',
             '遞迴分塊大小', '遞迴文字分塊策略的分塊字元數', 50, 10000, false),
            ('rag', 'RECURSIVE_TEXT_CHUNK_OVERLAP', '200', 'int', '200',
             '遞迴分塊重疊大小', '遞迴文字分塊策略的相鄰分塊重疊字元數', 0, 5000, false)
    """)


def downgrade() -> None:
    """Remove recursive text chunking settings from system_settings."""
    op.execute("""
        DELETE FROM system_settings
        WHERE setting_key IN ('RECURSIVE_TEXT_CHUNK_SIZE', 'RECURSIVE_TEXT_CHUNK_OVERLAP')
    """)
