"""
FastAPI 應用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.lifespan import lifespan
from app.utils.logger import setup_logger

# 設定 Logger
setup_logger()

# 建立 FastAPI 應用
app = FastAPI(
    title="Metora Backend",
    description="Metora Backend Service",
    version="0.1.0",
    lifespan=lifespan,  # 註冊生命週期管理
    debug=(settings.LOG_LEVEL == "DEBUG"),
)

# CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 註冊自定義 Middleware
# ==========================================
# 注意：Middleware 執行順序為先註冊的後執行（洋蔥模型）
# 請求流向：rate_limit → logging → user_context → request_id → 路由處理 → request_id → user_context → logging → rate_limit
from app.middleware.request_id import request_id_middleware
from app.middleware.user_context import user_context_middleware
from app.middleware.logging import logging_middleware
from app.middleware.rate_limit import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)  # 1. 最外層：速率限制
app.middleware("http")(logging_middleware)     # 2. 記錄日誌（需要使用 user_context）
app.middleware("http")(user_context_middleware)  # 3. 提取使用者上下文（供日誌使用）
app.middleware("http")(request_id_middleware)  # 4. 最內層：生成 request_id（必須最先設置）


# ==========================================
# 全局異常處理器
# ==========================================
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    general_exception_handler,
)

# 註冊異常處理器（順序很重要：從具體到一般）
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ==========================================
# 基礎路由
# ==========================================

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "Welcome to Metora Backend API",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """
    基礎健康檢查（Liveness Probe）
    
    用於 K8s/Docker 檢測服務是否存活
    特點：
    - 極快速響應（不檢查外部依賴）
    - 只檢查服務本身是否運行
    - 避免因依賴故障導致容器誤重啟
    
    K8s 配置範例：
    ```yaml
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
    ```
    """
    return {
        "status": "healthy",
        "service": "Metora Backend",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


# ==========================================
# 註冊 API v1 路由
# ==========================================
from app.api.v1.endpoints import api_router

app.include_router(api_router)
