# -*- coding: utf-8 -*-
"""
認證相關的依賴注入
用於保護需要認證的 API 路由
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserInfo


async def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
) -> UserInfo:
    """
    從 httpOnly Cookie 獲取當前使用者（依賴注入函式）

    Args:
        access_token: 從 cookie 自動提取的 JWT token
        db: 資料庫 session

    Returns:
        當前使用者資訊

    Raises:
        HTTPException: 當 token 無效或使用者不存在時

    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: Annotated[UserInfo, Depends(get_current_user)]
        ):
            return {"message": f"Hello, {current_user.username}"}
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(access_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Annotated[UserInfo, Depends(get_current_user)]
) -> UserInfo:
    """
    獲取當前啟用的使用者（依賴注入函式）

    Args:
        current_user: 當前使用者

    Returns:
        當前使用者資訊

    Raises:
        HTTPException: 當使用者帳號被停用時

    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: Annotated[UserInfo, Depends(get_current_active_user)]
        ):
            return {"message": f"Hello, {current_user.username}"}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[UserInfo, Depends(get_current_active_user)]
) -> UserInfo:
    """
    獲取當前超級管理員（依賴注入函式）

    Args:
        current_user: 當前啟用使用者

    Returns:
        當前使用者資訊

    Raises:
        HTTPException: 當使用者不是超級管理員時

    Usage:
        @router.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: Annotated[UserInfo, Depends(get_current_superuser)]
        ):
            # Only superusers can delete users
            ...
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def require_roles(*roles: str):
    """
    工廠函數:建立一個檢查使用者角色的依賴函式

    Args:
        *roles: 需要的角色名稱(可以是多個)

    Returns:
        一個依賴注入函式,用於檢查使用者是否具有指定角色

    Usage:
        # 需要 admin 角色
        @router.post("/users")
        async def create_user(
            current_user: Annotated[UserInfo, Depends(require_roles("admin"))]
        ):
            ...

        # 需要 admin 或 moderator 角色其中之一
        @router.put("/posts/{post_id}")
        async def update_post(
            current_user: Annotated[UserInfo, Depends(require_roles("admin", "moderator"))]
        ):
            ...
    """
    async def role_checker(
        current_user: Annotated[UserInfo, Depends(get_current_active_user)]
    ) -> UserInfo:
        """
        檢查當前使用者是否具有所需角色

        Args:
            current_user: 當前啟用使用者

        Returns:
            當前使用者資訊

        Raises:
            HTTPException: 當使用者沒有所需角色時
        """
        # 超級管理員可以繞過所有角色檢查
        if current_user.is_superuser:
            return current_user

        # 檢查使用者是否具有任一所需角色
        user_roles = set(current_user.roles)
        required_roles = set(roles)

        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(required_roles)}"
            )

        return current_user

    return role_checker


# 常用角色依賴的別名
require_admin = require_roles("admin")
