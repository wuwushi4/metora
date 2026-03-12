"""
資料庫連線池管理模組
使用 SQLAlchemy 2.0 async 引擎
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from loguru import logger

from app.core.config import settings

# 全局變數
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_database() -> AsyncEngine:
    """
    初始化資料庫連線池
    在應用啟動時調用
    """
    global _engine, _session_factory

    logger.info("正在建立資料庫連線池...")

    # 組合 DATABASE_URL 包含超時參數
    # psycopg3 支援在連線字串中直接設定參數
    database_url = (
        f"{settings.DATABASE_URL}"
        f"?connect_timeout={settings.DB_CONNECT_TIMEOUT}"
        f"&application_name=Metora Backend"
        f"&options=-c statement_timeout%3D{settings.DB_COMMAND_TIMEOUT * 1000}"
    )
    
    _engine = create_async_engine(
        database_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        echo=settings.SHOW_SQL,  # 是否顯示 SQL 查詢日誌
        future=True,
    )

    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # 測試連線
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(f"✅ 資料庫連線池已建立 (pool_size={settings.DB_POOL_SIZE})")
    except Exception as e:
        logger.error(f"❌ 資料庫連線失敗: {e}")
        raise

    return _engine


async def close_database() -> None:
    """
    關閉資料庫連線池
    在應用關閉時調用
    """
    global _engine, _session_factory

    if _engine:
        logger.info("正在關閉資料庫連線池...")
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("✅ 資料庫連線池已關閉")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    取得資料庫 session (FastAPI 依賴注入)

    使用方式:
        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
    """
    if _session_factory is None:
        raise RuntimeError("資料庫尚未初始化,請先調用 init_database()")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_engine() -> AsyncEngine:
    """取得資料庫引擎"""
    if _engine is None:
        raise RuntimeError("資料庫尚未初始化")
    return _engine
