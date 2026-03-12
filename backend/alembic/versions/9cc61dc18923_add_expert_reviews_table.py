"""add expert_reviews table

Revision ID: 9cc61dc18923
Revises: dd5e9e4400da
Create Date: 2025-10-30 10:08:19.164265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cc61dc18923'
down_revision: Union[str, Sequence[str], None] = 'dd5e9e4400da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 建立 expert_reviews 表
    op.create_table(
        'expert_reviews',
        sa.Column('id', sa.UUID(), nullable=False, comment='審查記錄 ID'),
        sa.Column('feedback_id', sa.UUID(), nullable=False, comment='關聯的反饋 ID (一對一)'),
        sa.Column('expert_opinion', sa.Text(), nullable=False, comment='專家意見'),
        sa.Column('suggested_response', sa.Text(), nullable=True, comment='建議回覆內容(用於 DPO 微調)'),
        sa.Column('reviewed_by', sa.Integer(), nullable=False, comment='審查者使用者 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='建立時間'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='最後更新時間'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['feedback_id'], ['message_feedbacks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('feedback_id', name='uq_expert_review_feedback')
    )

    # 建立索引
    op.create_index('idx_expert_reviews_feedback_id', 'expert_reviews', ['feedback_id'], unique=False)
    op.create_index('idx_expert_reviews_reviewed_by', 'expert_reviews', ['reviewed_by'], unique=False)
    op.create_index('idx_expert_reviews_created_at', 'expert_reviews', ['created_at'], unique=False)
    op.create_index('idx_expert_reviews_reviewer_created', 'expert_reviews', ['reviewed_by', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 刪除索引
    op.drop_index('idx_expert_reviews_reviewer_created', table_name='expert_reviews')
    op.drop_index('idx_expert_reviews_created_at', table_name='expert_reviews')
    op.drop_index('idx_expert_reviews_reviewed_by', table_name='expert_reviews')
    op.drop_index('idx_expert_reviews_feedback_id', table_name='expert_reviews')

    # 刪除表
    op.drop_table('expert_reviews')
