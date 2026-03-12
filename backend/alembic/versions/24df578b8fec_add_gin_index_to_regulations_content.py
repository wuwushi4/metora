"""Add GIN index to regulations content

Revision ID: 24df578b8fec
Revises: 699d168a107a
Create Date: 2025-11-18 21:37:03.117540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24df578b8fec'
down_revision: Union[str, Sequence[str], None] = '699d168a107a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 創建 GIN 索引以支援 JSONB 查詢
    op.create_index(
        'ix_regulations_content_gin',
        'regulations',
        ['content'],
        postgresql_using='gin'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 刪除 GIN 索引
    op.drop_index('ix_regulations_content_gin', 'regulations')
