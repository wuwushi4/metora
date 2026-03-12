"""
User Context Middleware
嘗試從 JWT token 提取使用者資訊並存入 request.state
用於日誌追蹤，不會阻擋請求
"""
from typing import Optional

from fastapi import Request
from loguru import logger

from app.utils.jwt import decode_token, verify_token_type


async def user_context_middleware(request: Request, call_next):
    """
    使用者上下文中介軟體

    功能：
    1. 優先從 Cookie 提取 JWT token（與認證邏輯一致）
    2. 降級方案：從 Authorization header 提取 token（支援 API 調用場景）
    3. 解析 token 並提取 user_id
    4. 將使用者資訊存入 request.state.user（供日誌記錄使用）

    特點：
    - 不會驗證 token 有效性（不查詢資料庫）
    - 不會阻擋請求（即使 token 無效也會繼續）
    - 只用於日誌追蹤，不用於權限控制
    - 權限控制仍由 auth dependencies 負責
    """
    # 初始化使用者上下文為 None
    request.state.user = None

    # 嘗試提取 token
    # 優先從 Cookie 讀取（與認證邏輯一致）
    token = request.cookies.get("access_token")

    # 降級方案：從 Authorization header 讀取（支援 API 調用場景）
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    # 如果成功獲取 token，嘗試解析
    if token:
        try:
            # 解析 token（只解析，不驗證有效性）
            payload = decode_token(token)
            if payload and verify_token_type(payload, "access"):
                # 提取 user_id
                user_id = payload.get("sub")
                username = payload.get("username")

                if user_id:
                    # 創建簡單的使用者上下文（只包含基本資訊）
                    request.state.user = {
                        "id": int(user_id),
                        "username": username or "unknown"
                    }
        except Exception as e:
            # 解析失敗不影響請求處理，只記錄 debug 日誌
            logger.debug(f"Failed to parse token for logging: {str(e)}")

    # 繼續處理請求
    response = await call_next(request)

    return response

