"""Add system settings tables

Revision ID: b7f8e9d0a1c2
Revises: 8329989679e2
Create Date: 2025-12-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7f8e9d0a1c2'
down_revision: Union[str, Sequence[str], None] = '8329989679e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 建立 system_settings 表
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False, comment='設定 ID'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='設定分類 (auth, rag, chat, upload)'),
        sa.Column('setting_key', sa.String(length=100), nullable=False, comment='設定鍵'),
        sa.Column('value', sa.Text(), nullable=False, comment='設定值 (JSON 格式儲存)'),
        sa.Column('value_type', sa.String(length=20), nullable=False, comment='值類型 (int, float, bool, string, array)'),
        sa.Column('default_value', sa.Text(), nullable=True, comment='預設值'),
        sa.Column('display_name', sa.String(length=100), nullable=True, comment='顯示名稱 (繁體中文)'),
        sa.Column('description', sa.Text(), nullable=True, comment='說明'),
        sa.Column('min_value', sa.Float(), nullable=True, comment='最小值 (數值型態)'),
        sa.Column('max_value', sa.Float(), nullable=True, comment='最大值 (數值型態)'),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='驗證規則 (JSON 格式)'),
        sa.Column('requires_restart', sa.Boolean(), nullable=False, server_default='false', comment='是否需要重啟'),
        sa.Column('is_sensitive', sa.Boolean(), nullable=False, server_default='false', comment='是否敏感 (不在前端顯示)'),
        sa.Column('updated_by', sa.Integer(), nullable=True, comment='修改者 ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='建立時間'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新時間'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('setting_key')
    )
    op.create_index('ix_system_settings_category', 'system_settings', ['category'], unique=False)
    op.create_index('ix_system_settings_id', 'system_settings', ['id'], unique=False)
    op.create_index('ix_system_settings_setting_key', 'system_settings', ['setting_key'], unique=False)

    # 建立 system_settings_audit 表
    op.create_table(
        'system_settings_audit',
        sa.Column('id', sa.Integer(), nullable=False, comment='審計日誌 ID'),
        sa.Column('setting_key', sa.String(length=100), nullable=False, comment='設定鍵'),
        sa.Column('old_value', sa.Text(), nullable=True, comment='舊值'),
        sa.Column('new_value', sa.Text(), nullable=True, comment='新值'),
        sa.Column('changed_by', sa.Integer(), nullable=True, comment='修改者 ID'),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, comment='修改時間'),
        sa.Column('change_reason', sa.Text(), nullable=True, comment='修改原因'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_settings_audit_id', 'system_settings_audit', ['id'], unique=False)
    op.create_index('ix_system_settings_audit_setting_key', 'system_settings_audit', ['setting_key'], unique=False)

    # 插入初始設定資料
    op.execute("""
        INSERT INTO system_settings (category, setting_key, value, value_type, default_value, display_name, description, min_value, max_value, requires_restart) VALUES
        -- 認證與安全 (category: auth)
        ('auth', 'ALLOW_PUBLIC_REGISTRATION', 'false', 'bool', 'false', '允許公開註冊', '是否開放使用者自行註冊帳號', NULL, NULL, false),
        ('auth', 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30', 'int', '30', '訪問令牌過期時間(分鐘)', '訪問令牌的有效期限(分鐘)', 5, 1440, true),
        ('auth', 'RATE_LIMIT_ENABLED', 'true', 'bool', 'true', '啟用速率限制', '是否啟用 API 速率限制', NULL, NULL, false),

        -- RAG 系統 (category: rag)
        ('rag', 'RAG_RETRIEVER_TOP_K', '3', 'int', '3', '檢索結果數量 (Top-K)', '向量檢索返回的文檔數量', 1, 20, false),
        ('rag', 'VECTOR_SEARCH_SCORE_THRESHOLD', '0.6', 'float', '0.6', '向量相似度閾值', '向量檢索的相關性閾值 (0.0-1.0)', 0.0, 1.0, false),
        ('rag', 'RERANKER_ENABLED', 'true', 'bool', 'true', '啟用重排序器', '是否啟用檢索結果重排序', NULL, NULL, false),

        -- LangGraph 對話 (category: chat)
        ('chat', 'GRAPH_MEMORY_TURNS', '5', 'int', '5', '對話記憶輪數', 'LLM 最終回應使用的對話輪數', 1, 10, false),
        ('chat', 'GRAPH_EXECUTION_TIMEOUT', '240', 'int', '240', '執行超時時間(秒)', 'Graph 執行的最大等待時間', 30, 600, false),

        -- 檔案上傳 (category: upload)
        ('upload', 'CHAT_FILE_UPLOAD_ENABLED', 'true', 'bool', 'true', '啟用聊天文件上傳', '是否允許在聊天中上傳文件', NULL, NULL, false),
        ('upload', 'CHAT_IMAGE_MAX_SIZE', '10485760', 'int', '10485760', '圖片最大大小(位元組)', '上傳圖片的最大檔案大小 (預設 10MB)', 1048576, 52428800, false),
        ('upload', 'CHAT_PDF_ENABLED', 'false', 'bool', 'false', '啟用 PDF 上傳', '是否允許上傳 PDF 文件', NULL, NULL, false)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # 刪除索引
    op.drop_index('ix_system_settings_audit_setting_key', table_name='system_settings_audit')
    op.drop_index('ix_system_settings_audit_id', table_name='system_settings_audit')
    op.drop_index('ix_system_settings_setting_key', table_name='system_settings')
    op.drop_index('ix_system_settings_id', table_name='system_settings')
    op.drop_index('ix_system_settings_category', table_name='system_settings')

    # 刪除表
    op.drop_table('system_settings_audit')
    op.drop_table('system_settings')
