"""
FastAPI 應用啟動入口
支援直接執行: python run.py
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
"""
import uvicorn

from app.core.config import settings


if __name__ == "__main__":
    # 開發模式:排除重載敏感檔案
    reload_config = {}
    if settings.SERVER_RELOAD:
        reload_config = {
            "reload": True,
            # 排除會觸發重載資源的核心檔案
            "reload_excludes": [
                "*.pyc",
                "*.pyo",
                "__pycache__",
                ".git",
                ".env",
                "*.log",
                # 排除模型相關檔案 (修改這些需要手動重啟)
                "app/models/embeddings.py",
                "app/models/reranker.py",
                "app/models/model_loader.py",
                # 排除資源管理器 (修改這些需要手動重啟)
                "app/core/resource_manager.py",
                "app/core/database.py",
                "app/core/redis.py",
                "app/vector_stores/chroma.py",
                "app/core/config.py",  # 配置變更應該重啟,不是 reload
            ],
        }

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        **reload_config,
    )
