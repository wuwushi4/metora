"""
Request ID 追蹤 Middleware
為每個請求生成唯一 ID，支援分散式追蹤
"""
import uuid
from contextvars import ContextVar

from fastapi import Request
from loguru import logger

# 使用 ContextVar 儲存請求 ID（執行緒安全）
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


async def request_id_middleware(request: Request, call_next):
    """
    Request ID 追蹤中介軟體
    
    功能：
    1. 從 header 獲取或生成新的 request ID
    2. 儲存到 ContextVar（執行緒安全）
    3. 添加到響應 header
    
    支援：
    - 前端可透過 X-Request-ID header 傳入自定義 ID
    - 後端自動生成 UUID 作為預設 ID
    - 便於追蹤日誌和問題排查
    """
    # 從 header 獲取或生成新的 request ID
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    
    # 儲存到 ContextVar
    request_id_var.set(request_id)
    
    # 處理請求
    response = await call_next(request)
    
    # 添加到響應 header
    response.headers['X-Request-ID'] = request_id
    
    return response

