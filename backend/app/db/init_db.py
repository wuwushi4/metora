# -*- coding: utf-8 -*-
"""
資料庫初始化腳本
建立預設角色和管理員使用者
"""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models import User, Role


async def init_db(db: AsyncSession) -> None:
    """
    初始化資料庫
    建立預設角色和管理員使用者
    """
    try:
        # 檢查是否已經初始化
        result = await db.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info("資料庫已經初始化,跳過")
            return

        logger.info("開始初始化資料庫...")

        # 建立預設角色
        admin_role = Role(
            name="admin",
            description="系統管理員",
            permissions='["*"]'  # 所有權限
        )
        user_role = Role(
            name="user",
            description="一般使用者",
            permissions='["read:own"]'  # 只能讀取自己的資料
        )

        db.add_all([admin_role, user_role])
        await db.flush()  # 取得 role ID

        # 建立預設管理員
        # 預設密碼: admin123
        # 預先計算好的 bcrypt hash
        # 這是 "admin123" 的 bcrypt hash（使用 bcrypt 原生 API 生成）
        preset_hash = "$2b$12$aIEcpoEO1/bZ1ojbQFp1XuDqKNm0fL8D60ZVjS4cvewDG42cCp3v."

        now = datetime.now(timezone.utc)

        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=preset_hash,
            full_name="系統管理員",
            is_active=True,
            is_superuser=True,
            created_at=now,
            updated_at=now,
            roles=[admin_role]
        )

        db.add(admin_user)
        await db.commit()

        logger.info("✅ 預設資料已建立")
        logger.info("   管理員帳號: admin / admin123")
        logger.info("   ⚠️  請記得修改預設密碼!")

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ 資料庫初始化失敗: {e}")
        raise
