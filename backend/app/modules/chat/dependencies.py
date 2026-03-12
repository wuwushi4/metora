# -*- coding: utf-8 -*-
"""
Chat 模組的依賴注入
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_redis
from app.core.config import settings
from app.modules.chat.service import ChatService
from app.modules.chat.cache import ChatCacheService
from app.modules.chat.attachment_converter import AttachmentConverter


async def get_attachment_converter() -> AttachmentConverter:
    """
    取得 AttachmentConverter 實例

    Returns:
        AttachmentConverter 實例
    """
    return AttachmentConverter(settings)


async def get_chat_service(
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    attachment_converter: AttachmentConverter = Depends(get_attachment_converter)
) -> ChatService:
    """
    取得 ChatService 實例

    Args:
        db: 資料庫 Session
        redis: Redis 客戶端
        attachment_converter: 附件轉換器

    Returns:
        ChatService 實例
    """
    cache = ChatCacheService(
        redis_client=redis,
        ttl_hours=settings.REDIS_CHAT_CACHE_TTL_HOURS
    )
    return ChatService(db, cache, settings, attachment_converter)
