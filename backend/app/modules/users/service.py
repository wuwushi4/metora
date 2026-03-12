# -*- coding: utf-8 -*-
"""
使用者管理服務層
處理使用者 CRUD 的業務邏輯
"""
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.user import User
from app.db.models.role import Role
from app.modules.users.schemas import UserCreate, UserUpdate, UserListParams
from app.utils.security import hash_password
from app.utils.exceptions import (
    DuplicateResourceError,
    ResourceNotFoundError,
    ValidationError,
)


class UserService:
    """使用者管理服務類別"""

    def __init__(self, db: AsyncSession):
        """
        初始化使用者服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def get_users(
        self,
        params: UserListParams
    ) -> Tuple[List[User], int]:
        """
        獲取使用者列表(支援分頁與篩選)

        Args:
            params: 查詢參數(分頁與篩選條件)

        Returns:
            (使用者列表, 總筆數)
        """
        # 使用查詢預載入 selectinload 避免 N+1 查詢問題
        stmt = select(User).options(selectinload(User.roles))

        # 篩選條件
        filters = []

        # username 模糊搜尋
        if params.username:
            filters.append(User.username.ilike(f"%{params.username}%"))

        # email 模糊搜尋
        if params.email:
            filters.append(User.email.ilike(f"%{params.email}%"))

        # is_active 精確搜尋
        if params.is_active is not None:
            filters.append(User.is_active == params.is_active)

        # role 精確搜尋(需要 join roles 表)
        if params.role:
            stmt = stmt.join(User.roles).filter(Role.name == params.role)

        # 套用所有篩選條件
        if filters:
            stmt = stmt.filter(*filters)

        # 計算總筆數
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分頁
        offset = (params.page - 1) * params.page_size
        stmt = stmt.offset(offset).limit(params.page_size)

        # 排序:依照建立時間降序排列
        stmt = stmt.order_by(User.created_at.desc())

        # 執行查詢
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return list(users), total

    async def get_user_by_id(self, user_id: int) -> User:
        """
        根據 ID 獲取使用者

        Args:
            user_id: 使用者 ID

        Returns:
            使用者物件

        Raises:
            ResourceNotFoundError: 若使用者不存在時
        """
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundError("使用者", str(user_id))

        return user

    async def create_user(self, request: UserCreate) -> User:
        """
        建立新使用者

        Args:
            request: 使用者建立資料

        Returns:
            新建立的使用者物件

        Raises:
            DuplicateResourceError: 若 username 或 email 已存在時
        """
        # 檢查 username 是否已存在
        stmt = select(User).where(User.username == request.username)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise DuplicateResourceError(
                resource="使用者",
                field="使用者名稱",
                value=request.username
            )

        # 檢查 email 是否已存在
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

        # 如果指定角色則分配
        if request.roles:
            await self._assign_roles_to_user(new_user, request.roles)

        await self.db.commit()
        await self.db.refresh(new_user)

        # 重新載入角色資訊
        await self.db.refresh(new_user, ["roles"])

        return new_user

    async def update_user(
        self,
        user_id: int,
        request: UserUpdate
    ) -> User:
        """
        更新使用者資訊


        Args:
            user_id: 使用者 ID
            request: 使用者更新資料

        Returns:
            更新後的使用者物件

        Raises:
            ResourceNotFoundError: 若使用者不存在時
            DuplicateResourceError: 若更新的 email 已存在時
        """
        # 獲取使用者
        user = await self.get_user_by_id(user_id)

        # 如果更新 email,檢查是否重複
        if request.email and request.email != user.email:
            stmt = select(User).where(User.email == request.email)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise DuplicateResourceError(
                    resource="使用者",
                    field="電子郵件",
                    value=request.email
                )

        # 只更新有提供的欄位(部分更新)
        if request.email is not None:
            user.email = request.email

        if request.full_name is not None:
            user.full_name = request.full_name

        if request.is_active is not None:
            user.is_active = request.is_active

        # 更新時間
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        # 重新載入角色資訊
        await self.db.refresh(user, ["roles"])

        return user

    async def delete_user(self, user_id: int) -> bool:
        """
        刪除使用者(軟刪除:設定 is_active=False)

        Args:
            user_id: 使用者 ID

        Returns:
            是否成功刪除

        Raises:
            ResourceNotFoundError: 若使用者不存在時
            ValidationError: 若嘗試刪除超級管理員時
        """
        # 獲取使用者
        user = await self.get_user_by_id(user_id)

        # 不允許刪除超級管理員
        if user.is_superuser:
            raise ValidationError("無法刪除超級管理員帳號")

        # 軟刪除:設定 is_active = False
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

        return True

    async def assign_roles(
        self,
        user_id: int,
        role_names: List[str]
    ) -> User:
        """
        分配角色給使用者

        Args:
            user_id: 使用者 ID
            role_names: 角色名稱列表

        Returns:
            更新後的使用者物件

        Raises:
            ResourceNotFoundError: 若使用者或角色不存在時
        """
        # 獲取使用者
        user = await self.get_user_by_id(user_id)

        # 分配角色
        await self._assign_roles_to_user(user, role_names)

        # 更新時間
        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        # 重新載入角色資訊
        await self.db.refresh(user, ["roles"])

        return user

    async def _assign_roles_to_user(
        self,
        user: User,
        role_names: List[str]
    ) -> None:
        """
        內部方法:分配角色給使用者

        Args:
            user: 使用者物件
            role_names: 角色名稱列表

        Raises:
            ResourceNotFoundError: 若角色不存在時
        """
        # 查詢所有指定的角色
        stmt = select(Role).where(Role.name.in_(role_names))
        result = await self.db.execute(stmt)
        roles = result.scalars().all()

        # 檢查是否所有角色都存在
        found_role_names = {role.name for role in roles}
        missing_roles = set(role_names) - found_role_names

        if missing_roles:
            raise ResourceNotFoundError(
                "角色",
                ", ".join(missing_roles)
            )

        # 清除舊角色,分配新角色
        user.roles = list(roles)
