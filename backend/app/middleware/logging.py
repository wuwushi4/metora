"""
請求日誌 Middleware
記錄所有 API 請求的詳細資訊
"""
import time
from typing import Optional

from fastapi import Request
from loguru import logger

from app.middleware.request_id import request_id_var


# 白名單路徑（不記錄或使用 DEBUG 級別）
SILENT_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
}

DEBUG_PATHS = {
    "/health",
    "/api/v1/status",
}


def _get_client_ip(request: Request) -> str:
    """
    獲取客戶端真實 IP 地址
    
    優先順序：
    1. X-Forwarded-For header（代理/負載均衡器場景）
    2. X-Real-IP header（Nginx 場景）
    3. request.client.host（直接連接）
    """
    # 檢查是否經過代理（X-Forwarded-For 可能包含多個 IP）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一個 IP（客戶端真實 IP）
        return forwarded_for.split(",")[0].strip()
    
    # 檢查 Nginx 設置的 X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接連接的情況
    return request.client.host if request.client else "unknown"


def _get_user_identifier(request: Request) -> str:
    """
    獲取使用者識別資訊
    
    嘗試從 request.state.user 獲取已驗證的使用者 ID
    如果使用者未登入，返回 "anonymous"
    """
    # 檢查是否有已驗證的使用者（由 auth middleware 設置）
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        # 支援兩種可能的結構
        if hasattr(user, "id"):
            return f"user:{user.id}"
        elif isinstance(user, dict) and "id" in user:
            return f"user:{user['id']}"
    
    return "anonymous"


async def logging_middleware(request: Request, call_next):
    """
    請求日誌中介軟體
    
    功能：
    1. 記錄請求開始（方法 + 路徑 + 使用者 + IP）
    2. 記錄請求結束（狀態碼 + 處理時間 + 使用者）
    3. 在響應 header 中添加處理時間
    
    過濾規則：
    - 靜態資源不記錄（/docs, /openapi.json）
    - 健康檢查使用 DEBUG 級別
    
    日誌格式：
    - 請求開始：→ METHOD /path | user_identifier | client_ip
    - 請求結束：← METHOD /path [status] time | user_identifier
    """
    # 靜態資源直接跳過
    if request.url.path in SILENT_PATHS:
        return await call_next(request)
    
    # 記錄請求開始
    start_time = time.time()
    
    # 獲取客戶端 IP
    client_ip = _get_client_ip(request)
    
    # 獲取使用者識別（此時可能還沒驗證，先標記為 anonymous）
    user_before = _get_user_identifier(request)
    
    # 健康檢查使用 DEBUG 級別
    if request.url.path in DEBUG_PATHS:
        logger.debug(
            f"→ {request.method} {request.url.path} | {user_before} | {client_ip}"
        )
    else:
        logger.info(
            f"→ {request.method} {request.url.path} | {user_before} | {client_ip}"
        )
    
    # 處理請求
    response = await call_next(request)
    
    # 計算處理時間
    process_time = time.time() - start_time
    
    # 再次獲取使用者識別（請求處理後可能已經驗證）
    user_after = _get_user_identifier(request)
    
    # 記錄請求結束
    if request.url.path in DEBUG_PATHS:
        logger.debug(
            f"← {request.method} {request.url.path} "
            f"[{response.status_code}] {process_time:.3f}s | {user_after}"
        )
    else:
        logger.info(
            f"← {request.method} {request.url.path} "
            f"[{response.status_code}] {process_time:.3f}s | {user_after}"
        )
    
    # 添加處理時間 header
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    return response

