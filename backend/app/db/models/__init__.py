# -*- coding: utf-8 -*-
"""
資料庫模型統一匯出
"""
from app.db.base import Base
from app.db.models.user import User, user_roles
from app.db.models.role import Role
from app.db.models.refresh_token import RefreshToken
from app.db.models.collection import Collection
from app.db.models.dataset import Dataset
from app.db.models.chat_session import ChatSession
from app.db.models.chat_message import ChatMessage
from app.db.models.message_feedback import MessageFeedback
from app.db.models.expert_review import ExpertReview
from app.db.models.message_attachment import MessageAttachment
from app.db.models.regulation import Regulation
from app.db.models.prompt_template import PromptTemplate
from app.db.models.system_setting import SystemSetting, SystemSettingAudit

# 匯出所有模型 (供 Alembic 自動偵測)
__all__ = [
    "Base",
    "User",
    "Role",
    "user_roles",
    "RefreshToken",
    "Collection",
    "Dataset",
    "ChatSession",
    "ChatMessage",
    "MessageFeedback",
    "ExpertReview",
    "MessageAttachment",
    "Regulation",
    "PromptTemplate",
    "SystemSetting",
    "SystemSettingAudit",
]
