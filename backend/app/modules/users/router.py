# -*- coding: utf-8 -*-
"""
使用者管理 API 路由
提供使用者 CRUD 的 RESTful API 端點
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.dependencies import (
    get_current_active_user,
    require_admin,
)
from app.modules.auth.schemas import UserInfo, MessageResponse
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListParams,
    AssignRolesRequest,
)
from app.i18n import t
from app.utils.response import ApiResponse, PaginatedResponse, success_response, paginated_response
from app.utils.exceptions import ValidationError

router = APIRouter(prefix="/users", tags=["使用者管理"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[UserResponse]],
    summary="獲取使用者列表",
    description="獲取使用者列表(支援分頁與篩選),需要 admin 角色"
)
async def get_users(
    page: int = Query(default=1, ge=1, description="頁碼(從 1 開始)"),
    page_size: int = Query(default=20, ge=1, le=100, description="每頁筆數(1-100)"),
    username: str | None = Query(default=None, description="使用者名稱(模糊搜尋)"),
    email: str | None = Query(default=None, description="電子郵件(模糊搜尋)"),
    is_active: bool | None = Query(default=None, description="是否啟用(精確搜尋)"),
    role: str | None = Query(default=None, description="角色(精確搜尋)"),
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取使用者列表

    權限要求:
    - 需要 admin 角色

    查詢參數:
    - page: 頁碼(從 1 開始)
    - page_size: 每頁筆數(1-100)
    - username: 使用者名稱(模糊搜尋)
    - email: 電子郵件(模糊搜尋)
    - is_active: 是否啟用(精確搜尋)
    - role: 角色(精確搜尋)

    回應:
    - 使用者列表與分頁資訊
    """
    params = UserListParams(
        page=page,
        page_size=page_size,
        username=username,
        email=email,
        is_active=is_active,
        role=role,
    )

    service = UserService(db)
    users, total = await service.get_users(params)

    # 將 ORM 物件轉換為 Response Schema
    user_list = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            roles=[role.name for role in user.roles],
        )
        for user in users
    ]

    return paginated_response(
        items=user_list,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="獲取單一使用者",
    description="根據 ID 獲取使用者詳細資訊,需要 admin 角色"
)
async def get_user(
    user_id: int,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取單一使用者

    權限要求:
    - 需要 admin 角色

    路徑參數:
    - user_id: 使用者 ID

    回應:
    - 使用者詳細資訊
    """
    service = UserService(db)
    user = await service.get_user_by_id(user_id)

    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        roles=[role.name for role in user.roles],
    )

    return success_response(data=user_response)


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="建立使用者",
    description="建立新使用者,需要 admin 角色"
)
async def create_user(
    request: UserCreate,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    建立新使用者

    權限要求:
    - 需要 admin 角色

    請求體:
    - username: 使用者名稱(3-50字元)
    - email: 電子郵件
    - password: 密碼(6-100字元)
    - full_name: 真實姓名(可選)
    - roles: 角色列表(可選,預設為 ["user"])

    回應:
    - 新建立的使用者資訊
    """
    service = UserService(db)
    new_user = await service.create_user(request)

    user_response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        created_at=new_user.created_at,
        roles=[role.name for role in new_user.roles],
    )

    return success_response(
        data=user_response,
        message=t('users.createSuccess')
    )


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="更新使用者",
    description="更新使用者資訊,需要 admin 角色或本人"
)
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    更新使用者資訊

    權限要求:
    - 需要 admin 角色,或者更新本人資料

    路徑參數:
    - user_id: 使用者 ID

    請求體:
    - email: 電子郵件(可選)
    - full_name: 真實姓名(可選)
    - is_active: 是否啟用(可選,僅 admin 可修改)

    回應:
    - 更新後的使用者資訊
    """
    # 權限檢查:只有 admin 或本人可以更新
    is_admin = "admin" in current_user.roles or current_user.is_superuser
    is_self = current_user.id == user_id

    if not (is_admin or is_self):
        raise ValidationError(t('users.cannotUpdateOthers'))

    # 只有 admin 可以修改 is_active
    if request.is_active is not None and not is_admin:
        raise ValidationError(t('users.adminOnlyActiveStatus'))

    service = UserService(db)
    updated_user = await service.update_user(user_id, request)

    user_response = UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        is_superuser=updated_user.is_superuser,
        created_at=updated_user.created_at,
        roles=[role.name for role in updated_user.roles],
    )

    return success_response(
        data=user_response,
        message=t('users.updateSuccess')
    )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[MessageResponse],
    summary="刪除使用者",
    description="刪除使用者(軟刪除),需要 admin 角色且不能刪除自己"
)
async def delete_user(
    user_id: int,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    刪除使用者(軟刪除)

    權限要求:
    - 需要 admin 角色
    - 不能刪除自己
    - 不能刪除超級管理員

    路徑參數:
    - user_id: 使用者 ID

    回應:
    - 刪除成功訊息
    """
    # 不能刪除自己
    if current_user.id == user_id:
        raise ValidationError(t('users.cannotDeleteSelf'))

    service = UserService(db)
    await service.delete_user(user_id)

    return success_response(
        data=MessageResponse(message=t('users.deleteSuccess')),
        message=t('users.deleteSuccess')
    )


@router.post(
    "/{user_id}/roles",
    response_model=ApiResponse[UserResponse],
    summary="分配角色",
    description="分配角色給使用者,需要 admin 角色"
)
async def assign_roles(
    user_id: int,
    request: AssignRolesRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    分配角色給使用者

    權限要求:
    - 需要 admin 角色

    路徑參數:
    - user_id: 使用者 ID

    請求體:
    - roles: 角色名稱列表

    回應:
    - 更新後的使用者資訊
    """
    service = UserService(db)
    updated_user = await service.assign_roles(user_id, request.roles)

    user_response = UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        is_superuser=updated_user.is_superuser,
        created_at=updated_user.created_at,
        roles=[role.name for role in updated_user.roles],
    )

    return success_response(
        data=user_response,
        message=t('users.roleAssignSuccess')
    )