# -*- coding: utf-8 -*-
"""
全局異常處理器
統一處理應用中的各種異常
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from loguru import logger

from app.utils.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    DatabaseError,
    RateLimitExceededError,
)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    處理自定義應用異常

    Args:
        request: FastAPI Request 物件
        exc: 應用異常實例

    Returns:
        JSONResponse 包含錯誤資訊
    """
    # 根據異常類型設定 HTTP 狀態碼
    status_code_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
    }

    # 獲取對應的狀態碼，預設為 400
    http_status = status_code_map.get(type(exc), status.HTTP_400_BAD_REQUEST)

    # 記錄錯誤日誌
    logger.warning(
        f"App Exception: [{exc.code}] {exc.message} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )

    # 構建響應內容
    content = {
        "success": False,
        "message": exc.message,
        "code": exc.code,
    }

    # 如果有額外詳情，加入響應
    if exc.details:
        content["details"] = exc.details

    # 認證錯誤需要添加 WWW-Authenticate header
    headers = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = "Bearer"
    
    # 速率限制錯誤需要添加 Retry-After header
    if isinstance(exc, RateLimitExceededError):
        retry_after = exc.details.get("retry_after", 60)
        headers["Retry-After"] = str(retry_after)
        # 添加速率限制相關 headers
        headers["X-RateLimit-Limit"] = str(exc.details.get("limit", 0))
        headers["X-RateLimit-Window"] = str(exc.details.get("window", 60))

    return JSONResponse(
        status_code=http_status,
        content=content,
        headers=headers
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    處理 Pydantic 驗證異常

    當請求資料不符合 Pydantic 模型定義時觸發

    Args:
        request: FastAPI Request 物件
        exc: Pydantic 驗證異常

    Returns:
        JSONResponse 包含驗證錯誤詳情
    """
    # 記錄錯誤日誌
    logger.warning(
        f"Validation Error: {len(exc.errors())} errors | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )

    # 簡化錯誤訊息格式
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "請求資料驗證失敗",
            "code": "VALIDATION_ERROR",
            "details": {"errors": errors}
        }
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError
) -> JSONResponse:
    """
    處理資料庫完整性約束異常

    當違反資料庫約束時觸發（如：唯一性約束、外鍵約束等）

    Args:
        request: FastAPI Request 物件
        exc: SQLAlchemy IntegrityError

    Returns:
        JSONResponse 包含錯誤資訊
    """
    # 記錄錯誤日誌
    logger.error(
        f"Database Integrity Error: {str(exc.orig)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )

    # 解析錯誤訊息，嘗試提供更友善的錯誤提示
    error_message = "資料庫約束違反"
    error_code = "INTEGRITY_ERROR"

    # 檢查是否為唯一性約束違反
    orig_error = str(exc.orig).lower()
    if "unique" in orig_error or "duplicate" in orig_error:
        error_message = "資料重複，該資源已存在"
        error_code = "DUPLICATE_RESOURCE"
    elif "foreign key" in orig_error:
        error_message = "參照完整性違反，關聯的資源不存在"
        error_code = "FOREIGN_KEY_ERROR"
    elif "not null" in orig_error:
        error_message = "必要欄位缺失"
        error_code = "NULL_CONSTRAINT_ERROR"

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "message": error_message,
            "code": error_code
        }
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    處理 SQLAlchemy 其他資料庫錯誤

    Args:
        request: FastAPI Request 物件
        exc: SQLAlchemy 異常

    Returns:
        JSONResponse 包含錯誤資訊
    """
    # 記錄錯誤日誌（包含完整 traceback）
    logger.error(
        f"Database Error: {type(exc).__name__}: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "資料庫操作失敗",
            "code": "DATABASE_ERROR"
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    處理未預期的一般異常

    作為最後的異常捕獲，避免應用崩潰

    Args:
        request: FastAPI Request 物件
        exc: 任何未被其他處理器捕獲的異常

    Returns:
        JSONResponse 包含通用錯誤訊息
    """
    # 記錄嚴重錯誤日誌（包含完整 traceback）
    logger.exception(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "伺服器內部錯誤",
            "code": "INTERNAL_SERVER_ERROR"
        }
    )
