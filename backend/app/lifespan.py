"""
FastAPI 應用生命週期管理
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.core.resource_manager import get_resource_manager
from app.middleware.rate_limit import register_rate_limit_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期管理

    啟動時初始化資源,關閉時清理資源
    """
    # ========================================
    # 啟動階段
    # ========================================
    logger.info("🎬 FastAPI 應用啟動中...")

    # 初始化全局資源
    resource_manager = get_resource_manager()
    await resource_manager.initialize()

    # 載入系統設定到記憶體
    logger.info("🔧 載入系統設定到記憶體快取...")
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.modules.settings.manager import settings_manager

        async with AsyncSession(resource_manager.db_engine) as db:
            await settings_manager.load_from_db(db)
    except Exception as e:
        logger.warning(f"⚠️  載入系統設定失敗（可能尚未執行資料庫遷移）: {e}")

    # 註冊速率限制路由
    register_rate_limit_routes(app)

    logger.info("🎉 FastAPI 應用已就緒!")

    # ========================================
    # 應用運行期間
    # ========================================
    yield

    # ========================================
    # 關閉階段
    # ========================================
    logger.info("👋 FastAPI 應用關閉中...")

    # 清理全局資源
    await resource_manager.cleanup()

    logger.info("💤 FastAPI 應用已關閉")
