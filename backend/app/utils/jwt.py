# -*- coding: utf-8 -*-
"""
JWT Token 工具模組
提供 JWT token 的生成、驗證、解析功能
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    創建 Access Token

    Args:
        data: 要編碼進 token 的資料 (通常包含 user_id, username 等)
        expires_delta: Token 有效期限，若不提供則使用配置中的預設值

    Returns:
        編碼後的 JWT token 字串

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    # 設定過期時間
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})

    # 編碼 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    創建 Refresh Token

    Args:
        data: 要編碼進 token 的資料 (通常包含 user_id)
        expires_delta: Token 有效期限，若不提供則使用配置中的預設值

    Returns:
        編碼後的 JWT token 字串

    Example:
        >>> token = create_refresh_token({"sub": "user123"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    # 設定過期時間
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})

    # 編碼 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解碼並驗證 JWT token

    Args:
        token: JWT token 字串

    Returns:
        解碼後的 payload 資料，若 token 無效則返回 None

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> print(payload["sub"])
        user123
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except InvalidTokenError:
        return None


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    驗證 token 類型是否符合預期

    Args:
        payload: 解碼後的 token payload
        expected_type: 預期的 token 類型 ("access" 或 "refresh")

    Returns:
        True 表示類型符合，False 表示類型不符

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> verify_token_type(payload, "access")
        True
        >>> verify_token_type(payload, "refresh")
        False
    """
    return payload.get("type") == expected_type
