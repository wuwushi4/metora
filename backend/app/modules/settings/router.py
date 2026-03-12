# -*- coding: utf-8 -*-
"""
系統設定 API 路由
提供系統設定管理的 RESTful API 端點
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.schemas import UserInfo
from app.modules.settings.service import SettingsService
from app.modules.settings.schemas import (
    SettingResponse,
    SettingsGroupResponse,
    SettingUpdate,
)
from app.utils.response import ApiResponse, success_response

router = APIRouter(prefix="/admin/settings", tags=["系統設定"])


@router.get(
    "",
    response_model=ApiResponse[SettingsGroupResponse],
    summary="獲取所有系統設定",
    description="獲取所有系統設定,按分類組織 (僅限管理員)"
)
async def get_all_settings(
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """獲取所有系統設定(按分類組織)"""
    service = SettingsService(db)
    settings = await service.get_all_settings()

    return success_response(data=settings)


@router.get(
    "/{key}",
    response_model=ApiResponse[SettingResponse],
    summary="獲取單一設定",
    description="根據設定鍵獲取單一設定資訊 (僅限管理員)"
)
async def get_setting(
    key: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """根據設定鍵獲取單一設定"""
    service = SettingsService(db)
    setting = await service.get_setting_by_key(key)

    return success_response(data=setting)


@router.put(
    "/{key}",
    response_model=ApiResponse[SettingResponse],
    summary="更新單一設定",
    description="更新單一設定值 (僅限管理員)"
)
async def update_setting(
    key: str,
    request: SettingUpdate,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新單一設定值"""
    service = SettingsService(db)
    updated_setting = await service.update_setting(
        key=key,
        request=request,
        user_id=current_user.id
    )

    return success_response(
        data=updated_setting,
        message="設定更新成功"
    )
