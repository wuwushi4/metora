# -*- coding: utf-8 -*-
"""
認證 API 路由
提供登入、註冊、登出、刷新 token 等端點
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.config import RateLimitLevel
from app.modules.auth.service import AuthService
from app.utils.rate_limit import rate_limit
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    RefreshTokenRequest,
    UserInfo,
    ChangePasswordRequest,
    MessageResponse,
)
from app.modules.auth.dependencies import get_current_active_user
from app.utils.response import ApiResponse, success_response
from app.utils.exceptions import ValidationError
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["認證"])


@router.post(
    "/register",
    response_model=ApiResponse[RegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="註冊新使用者",
    description="註冊新的使用者帳號 (需要在配置中啟用公開註冊)"
)
@rate_limit(RateLimitLevel.SENSITIVE)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    註冊新使用者

    ⚠️ 注意: 本系統為 B2B 企業內部管理系統,公開註冊功能預設為關閉。
    如需啟用,請在 .env 中設定 ALLOW_PUBLIC_REGISTRATION=true

    - **username**: 使用者名稱（3-50 字元，唯一）
    - **email**: 電子郵件（唯一）
    - **password**: 密碼（至少 6 字元）
    - **full_name**: 真實姓名（可選）
    """
    # 檢查是否允許公開註冊
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        raise ValidationError(
            "本系統不開放公開註冊。請聯繫管理員建立帳號。"
        )

    auth_service = AuthService(db)
    user = await auth_service.register(request)
    user_data = RegisterResponse.model_validate(user)

    return success_response(
        data=user_data,
        message="註冊成功"
    )


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    summary="使用者登入",
    description="使用者登入並獲取訪問令牌"
)
@rate_limit(RateLimitLevel.SENSITIVE)
async def login(
    request_data: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    使用者登入

    - **username**: 使用者名稱或電子郵件
    - **password**: 密碼

    返回:
    - **user**: 使用者資訊（tokens 存在 httpOnly cookie 中）
    """
    auth_service = AuthService(db)

    # 獲取客戶端資訊
    device_info = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None

    token_response, user_info = await auth_service.login(
        request_data,
        device_info=device_info,
        ip_address=ip_address
    )

    # 設定 access_token cookie
    response.set_cookie(
        key="access_token",
        value=token_response.access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # 設定 refresh_token cookie
    response.set_cookie(
        key="refresh_token",
        value=token_response.refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    login_data = LoginResponse(user=user_info)

    return success_response(
        data=login_data,
        message="登入成功"
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[MessageResponse],
    summary="刷新訪問令牌",
    description="使用刷新令牌獲取新的訪問令牌"
)
@rate_limit(RateLimitLevel.SENSITIVE)
async def refresh_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    刷新訪問令牌

    從 cookie 讀取 refresh_token 並更新 cookies
    """
    # 從 cookie 讀取 refresh_token
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        from app.utils.exceptions import AuthenticationError
        raise AuthenticationError("未找到 Refresh Token")
    
    auth_service = AuthService(db)
    token_response = await auth_service.refresh_access_token(refresh_token_value)
    
    # 更新 cookies
    response.set_cookie(
        key="access_token",
        value=token_response.access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=token_response.refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return success_response(
        data=MessageResponse(message="Token 刷新成功"),
        message="Token 刷新成功"
    )


@router.post(
    "/logout",
    response_model=ApiResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="使用者登出",
    description="登出並撤銷刷新令牌"
)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    使用者登出

    從 cookie 讀取 refresh_token 並撤銷，然後清除 cookies
    """
    refresh_token_value = request.cookies.get("refresh_token")
    if refresh_token_value:
        auth_service = AuthService(db)
        await auth_service.logout(refresh_token_value)
    
    # 清除 cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return success_response(
        data=MessageResponse(message="登出成功"),
        message="登出成功"
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserInfo],
    summary="獲取當前使用者資訊",
    description="獲取當前登入使用者的詳細資訊"
)
async def get_current_user_info(
    current_user: Annotated[UserInfo, Depends(get_current_active_user)]
):
    """
    獲取當前使用者資訊

    需要提供有效的訪問令牌（通過 Authorization header: Bearer <token>）
    """
    return success_response(
        data=current_user,
        message="獲取使用者資訊成功"
    )


@router.post(
    "/change-password",
    response_model=ApiResponse[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="修改密碼",
    description="修改當前使用者的密碼"
)
@rate_limit(RateLimitLevel.SENSITIVE)
async def change_password(
    request: ChangePasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserInfo, Depends(get_current_active_user)]
):
    """
    修改密碼

    需要提供有效的訪問令牌和舊密碼

    - **old_password**: 目前的密碼
    - **new_password**: 新密碼（至少 6 字元）
    """
    auth_service = AuthService(db)

    await auth_service.change_password(
        current_user.id,
        request.old_password,
        request.new_password
    )

    return success_response(
        data=MessageResponse(message="密碼修改成功"),
        message="密碼修改成功"
    )


@router.get(
    "/verify",
    response_model=ApiResponse[MessageResponse],
    summary="驗證 Token 有效性"
)
async def verify_token(
    current_user: Annotated[UserInfo, Depends(get_current_active_user)]
):
    """
    驗證當前 token 是否有效
    
    用於前端 initAuth 時驗證 cookie 中的 token
    """
    return success_response(
        data=MessageResponse(message="Token 有效"),
        message="Token 有效"
    )
