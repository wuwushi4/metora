# -*- coding: utf-8 -*-
"""
認證服務層
處理認證相關的業務邏輯
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token, verify_token_type
from app.core.config import settings
from app.utils.exceptions import (
    AuthenticationError,
    DuplicateResourceError,
    InvalidTokenError,
    TokenExpiredError,
    InactiveUserError,
    ResourceNotFoundError,
    ValidationError,
)


class AuthService:
    """認證服務類別"""

    def __init__(self, db: AsyncSession):
        """
        初始化認證服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def register(self, request: RegisterRequest) -> User:
        """
        註冊新使用者

        Args:
            request: 註冊請求資料

        Returns:
            新建立的使用者物件

        Raises:
            ValueError: 當使用者名稱或電子郵件已存在時
        """
        # 檢查使用者名稱是否已存在
        stmt = select(User).where(User.username == request.username)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise DuplicateResourceError(
                resource="使用者",
                field="使用者名稱",
                value=request.username
            )

        # 檢查電子郵件是否已存在
        stmt = select(User).where(User.email == request.email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise DuplicateResourceError(
                resource="使用者",
                field="電子郵件",
                value=request.email
            )

        # 建立新使用者
        now = datetime.now(timezone.utc)
        new_user = User(
            username=request.username,
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
            is_active=True,
            is_superuser=False,
            created_at=now,
            updated_at=now,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def login(
        self,
        request: LoginRequest,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[TokenResponse, UserInfo]:
        """
        使用者登入

        Args:
            request: 登入請求資料
            device_info: 裝置資訊（可選）
            ip_address: IP 位址（可選）

        Returns:
            Token 響應和使用者資訊的元組

        Raises:
            ValueError: 當使用者名稱/密碼錯誤或帳號被停用時
        """
        # 查找使用者（支援使用者名稱或電子郵件登入）
        stmt = select(User).options(selectinload(User.roles)).where(
            (User.username == request.username) | (User.email == request.username)
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        # 驗證使用者存在且密碼正確
        if not user or not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("使用者名稱或密碼錯誤")

        # 檢查帳號是否啟用
        if not user.is_active:
            raise InactiveUserError()

        # 生成 tokens
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # 儲存 refresh token 到資料庫
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=expires_at,
            created_at=now,  # 明確設定 created_at
            device_info=device_info,
            ip_address=ip_address,
        )
        self.db.add(db_refresh_token)

        # 更新最後登入時間
        user.last_login_at = datetime.now(timezone.utc)

        await self.db.commit()

        # 準備響應
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

        user_info = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=[role.name for role in user.roles]
        )

        return token_response, user_info

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        使用 refresh token 刷新 access token

        Args:
            refresh_token: Refresh token 字串

        Returns:
            新的 Token 響應

        Raises:
            ValueError: 當 token 無效、過期或類型錯誤時
        """
        # 解碼 token
        payload = decode_token(refresh_token)
        if not payload:
            raise InvalidTokenError("無效的 Refresh Token")

        # 驗證 token 類型
        if not verify_token_type(payload, "refresh"):
            raise InvalidTokenError("Token 類型錯誤")

        # 驗證 token 是否存在於資料庫
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise InvalidTokenError("Refresh Token 不存在")

        # 檢查是否過期
        if db_token.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredError("Refresh Token 已過期")

        # 獲取使用者資訊
        user_id = int(payload.get("sub"))
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("使用者", str(user_id))

        if not user.is_active:
            raise InactiveUserError()

        # 生成新的 tokens
        token_data = {"sub": str(user.id), "username": user.username}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": str(user.id)})

        # 更新資料庫中的 refresh token
        db_token.token = new_refresh_token
        db_token.expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    async def logout(self, refresh_token: str) -> bool:
        """
        登出（撤銷 refresh token）

        Args:
            refresh_token: Refresh token 字串

        Returns:
            是否成功登出

        """
        # 從資料庫中刪除 refresh token
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if db_token:
            await self.db.delete(db_token)
            await self.db.commit()
            return True

        return False

    async def get_current_user(self, token: str) -> Optional[UserInfo]:
        """
        根據 access token 獲取當前使用者資訊

        Args:
            token: Access token 字串

        Returns:
            使用者資訊，若 token 無效則返回 None
        """
        # 解碼 token
        payload = decode_token(token)
        if not payload:
            return None

        # 驗證 token 類型
        if not verify_token_type(payload, "access"):
            return None

        # 獲取使用者
        user_id = int(payload.get("sub"))
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        return UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=[role.name for role in user.roles]
        )

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改使用者密碼

        Args:
            user_id: 使用者ID
            old_password: 舊密碼
            new_password: 新密碼

        Returns:
            是否成功修改

        Raises:
            ValueError: 當舊密碼錯誤時
        """
        # 獲取使用者
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("使用者", str(user_id))

        # 驗證舊密碼
        if not verify_password(old_password, user.hashed_password):
            raise AuthenticationError("舊密碼錯誤")

        # 更新密碼
        user.hashed_password = hash_password(new_password)
        await self.db.commit()

        return True
