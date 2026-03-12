"""
Redis 連線池管理模組
"""
from __future__ import annotations

import redis.asyncio as redis
from loguru import logger

from app.core.config import settings

# 全局變數
_redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    """
    初始化 Redis 連線池
    在應用啟動時調用
    """
    global _redis_client

    logger.info("正在建立 Redis 連線池...")

    _redis_client = redis.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,  # 自動解碼 UTF-8
        encoding="utf-8",
    )

    # 測試連線
    try:
        await _redis_client.ping()
        logger.info(f"✅ Redis 連線池已建立 (max_connections={settings.REDIS_MAX_CONNECTIONS})")
    except Exception as e:
        logger.error(f"❌ Redis 連線失敗: {e}")
        raise

    return _redis_client


async def close_redis() -> None:
    """
    關閉 Redis 連線池
    在應用關閉時調用
    """
    global _redis_client

    if _redis_client:
        logger.info("正在關閉 Redis 連線池...")
        await _redis_client.close()
        _redis_client = None
        logger.info("✅ Redis 連線池已關閉")


def get_redis_client() -> redis.Redis:
    """取得 Redis 客戶端"""
    if _redis_client is None:
        raise RuntimeError("Redis 尚未初始化,請先調用 init_redis()")
    return _redis_client
