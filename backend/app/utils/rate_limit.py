"""
速率限制裝飾器工具
提供路由級別的速率限制標記
"""
from functools import wraps
from typing import Callable
from app.core.config import RateLimitLevel


def rate_limit(level: RateLimitLevel):
    """
    速率限制裝飾器
    
    用於標記 API 端點的速率限制級別，供 Middleware 讀取
    
    Args:
        level: 速率限制級別（RateLimitLevel Enum）
    
    Returns:
        裝飾器函數
    
    Usage:
        from app.utils.rate_limit import rate_limit
        from app.core.config import RateLimitLevel
        
        @router.post("/login")
        @rate_limit(RateLimitLevel.SENSITIVE)
        async def login(...):
            ...
        
        @router.get("/users")  # 不標記 = 使用預設限制
        async def get_users(...):
            ...
    
    Note:
        - 不標記的端點會使用 DEFAULT 級別
        - 白名單路徑（如 /health）會自動跳過速率限制
    """
    def decorator(func: Callable):
        # 將速率限制級別附加到函數的元數據
        func._rate_limit_level = level
        return func
    return decorator

