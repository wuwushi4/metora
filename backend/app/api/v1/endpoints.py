"""
API v1 路由統一註冊
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.resource_manager import get_resource_manager
from app.core.config import settings

# 建立 API v1 主路由
api_router = APIRouter(prefix="/api/v1")


# ==========================================
# 系統狀態端點
# ==========================================

@api_router.get("/status")
async def api_status():
    """
    完整狀態檢查（Readiness Probe + 運維監控）
    
    用途：
    - K8s readinessProbe（判斷是否可接收流量）
    - 開發/運維人員監控系統狀態
    - 排查依賴服務問題
    
    檢查項目：
    - 資料庫連線（實際執行 SELECT 1 測試）
    - Redis 連線（實際 ping 測試）
    - AI 模型載入狀態
    - ChromaDB 連線狀態
    
    狀態說明：
    - healthy: 所有服務正常
    - degraded: 部分服務異常但系統仍可運作
    - unhealthy: 關鍵服務異常，不應接收流量
    
    K8s 配置範例：
    ```yaml
    readinessProbe:
      httpGet:
        path: /api/v1/status
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
    ```
    """
    rm = get_resource_manager()
    
    health_status = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
        "vector_store_provider": settings.VECTOR_STORE_PROVIDER,
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "embedding_model": "unknown",
            "reranker_model": "unknown",
            "vector_store": "unknown",
        }
    }
    
    # 檢查資料庫（實際連線測試）
    try:
        if rm.db_engine:
            async with AsyncSession(rm.db_engine) as session:
                await session.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
        else:
            health_status["checks"]["database"] = "not_initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)[:100]}"
        health_status["status"] = "degraded"
    
    # 檢查 Redis（實際 ping 測試）
    try:
        if rm.redis_client:
            await rm.redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        else:
            health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)[:100]}"
        health_status["status"] = "degraded"
    
    # 檢查 AI 模型（只檢查是否載入）
    health_status["checks"]["embedding_model"] = (
        "loaded" if rm.embedding_model else "not_loaded"
    )
    health_status["checks"]["reranker_model"] = (
        "loaded" if rm.reranker_model else "not_loaded"
    )
    
    # 檢查向量資料庫連線
    try:
        if rm.vector_store:
            is_healthy = await rm.vector_store.heartbeat()
            health_status["checks"]["vector_store"] = "connected" if is_healthy else "unhealthy"
        else:
            health_status["checks"]["vector_store"] = "not_initialized"
    except Exception as e:
        health_status["checks"]["vector_store"] = f"unhealthy: {str(e)[:100]}"
        health_status["status"] = "degraded"
    
    # 根據檢查結果決定 HTTP 狀態碼
    # healthy/degraded: 200 (服務可用)
    # unhealthy: 503 (服務不可用)
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    
    return JSONResponse(content=health_status, status_code=status_code)


# ==========================================
# 註冊業務模組路由
# ==========================================

# 認證模組
from app.modules.auth.router import router as auth_router
api_router.include_router(auth_router)

# 使用者管理模組
from app.modules.users.router import router as users_router
api_router.include_router(users_router)

# Collection 管理模組
from app.modules.collections.router import router as collections_router
api_router.include_router(collections_router)

# Dataset 管理模組
from app.modules.datasets.router import router as datasets_router
api_router.include_router(datasets_router)

# Retrieval 檢索模組
from app.modules.retrieval.router import router as retrieval_router
api_router.include_router(retrieval_router)

# Chat 聊天模組
from app.modules.chat.router import router as chat_router
api_router.include_router(chat_router)

# Feedback 反饋模組
from app.modules.feedback.router import router as feedback_router
api_router.include_router(feedback_router)

# Data Engineering 資料工程模組
from app.modules.data_engineering.router import router as data_engineering_router
api_router.include_router(data_engineering_router)

# Regulation 法規管理模組
from app.modules.regulations.router import router as regulations_router
api_router.include_router(regulations_router)

# Prompts 系統提示詞模組
from app.modules.prompts.router import router as prompts_router
api_router.include_router(prompts_router)

# Dashboard 儀表板模組
from app.modules.dashboard.router import router as dashboard_router
api_router.include_router(dashboard_router)

# Settings 系統設定模組
from app.modules.settings.router import router as settings_router
api_router.include_router(settings_router)
