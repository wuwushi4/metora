"""
Loguru 日誌配置
"""
import sys

from loguru import logger

from app.core.config import settings


def request_id_filter(record):
    """
    為日誌添加 request_id
    
    從 ContextVar 獲取當前請求的 request_id
    如果不存在則使用 '-' 作為預設值
    """
    try:
        from app.middleware.request_id import request_id_var
        request_id = request_id_var.get('-')
    except Exception:
        request_id = '-'
    
    record["extra"]["request_id"] = request_id
    return True


def setup_logger() -> None:
    """
    配置 Loguru 日誌系統

    優化後的配置:
    - 移除粗體效果,降低視覺疲勞
    - 使用柔和的顏色方案(dim 降低亮度)
    - 簡化格式,減少顏色密度
    - 整合 request_id 追蹤
    """
    # 移除預設 handler
    logger.remove()

    # 新增 console handler (優化配色,不使用 <level> 標籤以避免粗體)
    # 使用 <dim> 降低時間和位置資訊的亮度
    # 只在必要時使用顏色(WARNING 以上)
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<dim>{time:YYYY-MM-DD HH:mm:ss}</dim> | "
            "<dim>{level: <8}</dim> | "
            "<cyan>[{extra[request_id]}]</cyan> | "
            "<dim>{name}:{function}:{line}</dim> | "
            "{message}"
        ),
        colorize=True,
        filter=request_id_filter,
    )

    # 可選:新增檔案 handler
    # logger.add(
    #     "logs/app_{time:YYYY-MM-DD}.log",
    #     rotation="00:00",  # 每天午夜輪替
    #     retention="30 days",  # 保留 30 天
    #     level=settings.LOG_LEVEL,
    #     format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | [{extra[request_id]}] | {name}:{function}:{line} | {message}",
    #     filter=request_id_filter,
    # )

    logger.info(f"Logger 已初始化 (level={settings.LOG_LEVEL})")
