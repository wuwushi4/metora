# -*- coding: utf-8 -*-
"""
資料工程模組自訂異常
"""
from typing import Optional, Dict, Any
from app.utils.exceptions import AppException


class ScrapingError(AppException):
    """爬蟲錯誤"""

    def __init__(
        self,
        pcode: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"爬取法規 {pcode} 失敗: {message}",
            code="SCRAPING_ERROR",
            details=details or {"pcode": pcode}
        )


class ConversionError(AppException):
    """轉換錯誤"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"轉換失敗: {message}",
            code="CONVERSION_ERROR",
            details=details
        )
