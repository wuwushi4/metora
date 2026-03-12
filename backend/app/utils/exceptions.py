# -*- coding: utf-8 -*-
"""
自定義異常類別
提供統一的異常處理機制
"""
from typing import Any, Optional, Dict


class AppException(Exception):
    """
    應用基礎異常

    所有自定義異常的基類
    """

    # 日誌嚴重性級別 (warning/error)
    # 子類可覆蓋此屬性來指定預設日誌級別
    severity: str = "warning"

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化異常

        Args:
            message: 錯誤訊息
            code: 錯誤代碼（用於前端識別錯誤類型）
            details: 額外的錯誤詳情
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message='{self.message}', code='{self.code}')"


class AuthenticationError(AppException):
    """
    認證錯誤

    當使用者認證失敗時拋出（如：無效的 token、密碼錯誤等）
    """

    def __init__(self, message: str = "認證失敗", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="AUTH_ERROR", details=details)


class AuthorizationError(AppException):
    """
    授權錯誤

    當使用者沒有足夠權限執行操作時拋出
    """

    def __init__(self, message: str = "權限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="PERMISSION_DENIED", details=details)


class ResourceNotFoundError(AppException):
    """
    資源未找到錯誤

    當請求的資源不存在時拋出
    """

    def __init__(
        self,
        resource: str,
        identifier: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if identifier:
            message = f"{resource} (ID: {identifier}) 不存在"
        else:
            message = f"{resource} 不存在"

        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            details=details or {"resource": resource, "identifier": identifier}
        )


class ValidationError(AppException):
    """
    驗證錯誤

    當資料驗證失敗時拋出（業務邏輯層級的驗證）
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class DatabaseError(AppException):
    """
    資料庫錯誤

    當資料庫操作失敗時拋出
    """

    severity: str = "error"  # 資料庫錯誤使用 error 級別

    def __init__(
        self,
        message: str = "資料庫操作失敗",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code="DATABASE_ERROR", details=details)


class DuplicateResourceError(AppException):
    """
    資源重複錯誤

    當嘗試建立已存在的資源時拋出（如：重複的使用者名稱、Email 等）
    """

    def __init__(
        self,
        resource: str,
        field: str,
        value: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} 的 {field} '{value}' 已存在"
        super().__init__(
            message=message,
            code="DUPLICATE_RESOURCE",
            details=details or {"resource": resource, "field": field, "value": value}
        )


class InvalidTokenError(AuthenticationError):
    """
    無效 Token 錯誤

    當 JWT token 無效、過期或格式錯誤時拋出
    """

    def __init__(self, message: str = "無效的 Token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.code = "INVALID_TOKEN"


class TokenExpiredError(AuthenticationError):
    """
    Token 過期錯誤

    當 JWT token 已過期時拋出
    """

    def __init__(self, message: str = "Token 已過期", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.code = "TOKEN_EXPIRED"


class InactiveUserError(AuthenticationError):
    """
    使用者未啟用錯誤

    當嘗試使用已停用的帳號時拋出
    """

    def __init__(self, message: str = "帳號已被停用", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.code = "INACTIVE_USER"


class RateLimitExceededError(AppException):
    """
    速率限制超過錯誤
    
    當 API 請求超過速率限制時拋出
    """
    
    def __init__(
        self,
        message: str = "請求次數過多，請稍後再試",
        retry_after: int = 60,
        limit: int = 0,
        window: int = 60,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details.update({
            "retry_after": retry_after,
            "limit": limit,
            "window": window
        })
        
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details=error_details
        )
