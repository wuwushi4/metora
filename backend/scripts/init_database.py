# -*- coding: utf-8 -*-
"""
資料庫初始化執行腳本
執行方式: python scripts/init_database.py
"""
import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_database, get_db
from app.db.init_db import init_db


async def main():
    """主函式"""
    print("=" * 50)
    print("開始初始化資料庫...")
    print("=" * 50)

    # 初始化資料庫連線池
    await init_database()

    # 獲取資料庫 session 並初始化
    async for db in get_db():
        await init_db(db)
        break  # 只執行一次

    print("=" * 50)
    print("資料庫初始化完成!")
    print("=" * 50)


if __name__ == "__main__":
    # Windows 平台需要設定事件循環策略
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
