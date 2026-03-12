"""rename_is_default_to_is_favorite_in_prompt_templates

Revision ID: 996f19ee635f
Revises: 823cda381a78
Create Date: 2025-11-20 16:15:36.986467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '996f19ee635f'
down_revision: Union[str, Sequence[str], None] = '823cda381a78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Rename is_default to is_favorite in prompt_templates table."""
    # 重命名欄位：is_default → is_favorite
    op.alter_column(
        'prompt_templates',
        'is_default',
        new_column_name='is_favorite',
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.text('false'),
        comment='是否收藏此提示詞'
    )


def downgrade() -> None:
    """Downgrade schema: Rename is_favorite back to is_default."""
    # 重命名欄位：is_favorite → is_default
    op.alter_column(
        'prompt_templates',
        'is_favorite',
        new_column_name='is_default',
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.text('false'),
        comment='是否為預設提示詞'
    )
