"""
速率限制 Middleware
基於 Redis 的滑動窗口速率限制，保護 API 免受濫用
"""
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings, RateLimitLevel
from app.core.resource_manager import get_resource_manager


# 白名單路徑（不受速率限制）
WHITELIST_PATHS = {
    "/",
    "/health",
    "/api/v1/status",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# 速率限制路由註冊表（路徑 -> 級別映射）
# 在應用啟動時會從裝飾器自動建立
_RATE_LIMIT_REGISTRY: dict[str, RateLimitLevel] = {}


def register_rate_limit_routes(app):
    """
    從 FastAPI app 中提取所有標記了速率限制的路由
    應在應用啟動時調用（lifespan 或 startup event）
    """
    global _RATE_LIMIT_REGISTRY
    _RATE_LIMIT_REGISTRY.clear()
    
    for route in app.routes:
        # 檢查是否為 APIRoute 且有 endpoint
        if hasattr(route, "endpoint") and hasattr(route.endpoint, "_rate_limit_level"):
            # 註冊路徑和級別的映射
            path = route.path
            level = route.endpoint._rate_limit_level
            _RATE_LIMIT_REGISTRY[path] = level
            logger.info(f"[Rate Limit Registry] {path} -> {level.value}")


def get_rate_limit_level(request: Request) -> RateLimitLevel:
    """
    從路由註冊表獲取速率限制級別
    
    優先順序：
    1. 白名單路徑 -> NONE（不限制）
    2. 註冊表中的路徑 -> 使用註冊的級別
    3. 預設 -> DEFAULT
    
    Args:
        request: FastAPI Request 物件
    
    Returns:
        RateLimitLevel: 速率限制級別
    """
    # 1. 檢查白名單（優先級最高）
    if request.url.path in WHITELIST_PATHS:
        return RateLimitLevel.NONE
    
    # 2. 檢查路由註冊表
    if request.url.path in _RATE_LIMIT_REGISTRY:
        level = _RATE_LIMIT_REGISTRY[request.url.path]
        logger.debug(f"[Rate Limit] {request.url.path} -> {level.value} (from registry)")
        return level
    
    # 3. 預設使用一般限制
    logger.debug(f"[Rate Limit] {request.url.path} -> default")
    return RateLimitLevel.DEFAULT


def get_rate_limit_config(level: RateLimitLevel) -> dict:
    """
    根據級別獲取速率限制配置
    
    Args:
        level: 速率限制級別
    
    Returns:
        dict: 包含 requests 和 window 的配置
    """
    configs = {
        RateLimitLevel.DEFAULT: {
            "requests": settings.RATE_LIMIT_DEFAULT,
            "window": 60
        },
        RateLimitLevel.SENSITIVE: {
            "requests": settings.RATE_LIMIT_SENSITIVE,
            "window": 60
        },
        RateLimitLevel.STRICT: {
            "requests": settings.RATE_LIMIT_STRICT,
            "window": 60
        },
    }
    return configs.get(level, configs[RateLimitLevel.DEFAULT])


class RateLimiter:
    """
    基於 Redis 的速率限制器
    使用 Sorted Set 實作精確的滑動窗口演算法
    """
    
    def __init__(self, requests: int, window: int):
        """
        初始化速率限制器
        
        Args:
            requests: 時間窗口內允許的請求數
            window: 時間窗口（秒）
        """
        self.requests = requests
        self.window = window
    
    async def check_rate_limit(self, key: str, redis_client) -> tuple[bool, int]:
        """
        檢查是否超過速率限制
        
        Args:
            key: Redis key（通常是 "rate_limit:{path}:{client_ip}"）
            redis_client: Redis 客戶端
        
        Returns:
            (是否允許請求, 剩餘配額)
        
        演算法：
        1. 移除時間窗口外的舊記錄
        2. 添加當前請求時間戳
        3. 計算窗口內的請求數
        4. 設定過期時間
        """
        current = time.time()
        window_start = current - self.window
        
        # 使用 pipeline 批次執行，提升性能
        pipeline = redis_client.pipeline()
        
        # 移除過期記錄
        pipeline.zremrangebyscore(key, 0, window_start)
        
        # 添加當前請求（使用 UUID 避免重複）
        pipeline.zadd(key, {str(uuid.uuid4()): current})
        
        # 計算當前窗口內的請求數
        pipeline.zcard(key)
        
        # 設定過期時間（窗口時間 + 1 秒緩衝）
        pipeline.expire(key, self.window + 1)
        
        # 執行 pipeline
        results = await pipeline.execute()
        count = results[2]  # zcard 的結果
        
        # 判斷是否超過限制
        allowed = count <= self.requests
        remaining = max(0, self.requests - count)
        
        return allowed, remaining


async def rate_limit_middleware(request: Request, call_next):
    """
    速率限制中介軟體
    
    功能：
    1. 白名單直接放行
    2. 敏感 API 嚴格限制（10 次/分鐘）
    3. 一般 API 寬鬆限制（500 次/分鐘）
    4. Redis 不可用時自動降級（記錄警告並放行）
    
    容錯機制：
    - 設定 RATE_LIMIT_ENABLED=false 可停用速率限制
    - Redis 不可用時自動降級，不影響服務
    """
    # 白名單直接放行
    if request.url.path in WHITELIST_PATHS:
        return await call_next(request)
    
    # 檢查是否啟用速率限制
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)
    
    # 容錯：Redis 不可用時記錄警告並放行
    resources = get_resource_manager()
    redis_client = resources.redis_client
    
    if not redis_client:
        logger.warning(f"Redis 未啟用，速率限制已停用 - {request.url.path}")
        return await call_next(request)
    
    # 獲取速率限制級別
    limit_level = get_rate_limit_level(request)
    
    # 如果是 NONE，直接放行
    if limit_level == RateLimitLevel.NONE:
        return await call_next(request)
    
    # 獲取對應的限制配置
    limit_config = get_rate_limit_config(limit_level)
    limit_type = limit_level.value  # 用於日誌記錄
    
    # 建立速率限制器
    limiter = RateLimiter(
        requests=limit_config["requests"],
        window=limit_config["window"]
    )
    
    # 使用 IP 作為限制鍵（可根據需求改為使用者 ID）
    client_ip = request.client.host if request.client else "unknown"
    redis_key = f"rate_limit:{request.url.path}:{client_ip}"
    
    try:
        # 檢查速率限制
        allowed, remaining = await limiter.check_rate_limit(redis_key, redis_client)
        
        if not allowed:
            # 超過限制
            logger.warning(
                f"速率限制觸發 [{limit_type}] - "
                f"{request.method} {request.url.path} - "
                f"IP: {client_ip}"
            )
            
            # 直接返回符合 ApiResponse 格式的 JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": f"請求次數過多，請稍後再試（限制：{limit_config['requests']} 次/{limit_config['window']} 秒）",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "retry_after": limit_config["window"],
                        "limit": limit_config["requests"],
                        "window": limit_config["window"]
                    }
                },
                headers={
                    "Retry-After": str(limit_config["window"]),
                    "X-RateLimit-Limit": str(limit_config["requests"]),
                    "X-RateLimit-Window": str(limit_config["window"])
                }
            )
        
        # 處理請求
        response = await call_next(request)
        
        # 添加速率限制資訊到 header
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + limit_config["window"]))
        
        return response
        
    except Exception as e:
        # Redis 操作失敗時記錄錯誤並放行（容錯）
        logger.error(f"速率限制檢查失敗，放行請求 - {request.url.path}: {e}")
        return await call_next(request)

