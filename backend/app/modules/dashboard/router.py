# -*- coding: utf-8 -*-
"""
Dashboard 模組的 API 路由
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.dependencies import get_current_active_user, require_admin
from app.modules.auth.schemas import UserInfo
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import (
    AdminDashboardStats,
    UserDashboardInfo,
    TimeRange,
)
from app.i18n import t
from app.utils.response import ApiResponse, success_response

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ==========================================
# Admin 端點
# ==========================================

@router.get(
    "/admin/stats",
    response_model=ApiResponse[AdminDashboardStats],
    status_code=status.HTTP_200_OK,
    summary="取得 Admin 儀表板統計 (管理員)",
    description="管理員查看全局統計數據,包含聊天互動指標和 AI 品質反饋指標",
)
async def get_admin_dashboard_stats(
    time_range: TimeRange = Query(TimeRange.ALL, description="時間範圍篩選"),
    current_user: UserInfo = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminDashboardStats]:
    """取得 Admin 儀表板統計"""
    service = DashboardService(db)
    stats = await service.get_admin_stats(time_range=time_range)
    return success_response(data=stats, message=t('dashboard.statsSuccess'))


# ==========================================
# User 端點
# ==========================================

@router.get(
    "/user/info",
    response_model=ApiResponse[UserDashboardInfo],
    status_code=status.HTTP_200_OK,
    summary="取得 User 儀表板資訊",
    description="一般使用者查看個人儀表板資訊",
)
async def get_user_dashboard_info(
    current_user: UserInfo = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserDashboardInfo]:
    """取得 User 儀表板資訊"""
    service = DashboardService(db)
    info = await service.get_user_info(
        user_id=current_user.id,
        username=current_user.username
    )
    return success_response(data=info, message=t('dashboard.userInfoSuccess'))
