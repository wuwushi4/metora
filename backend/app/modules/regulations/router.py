# -*- coding: utf-8 -*-
"""
Regulation 管理 API 路由
提供 Regulation CRUD 的 RESTful API 端點
"""
import json
from io import BytesIO
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.dependencies import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import UserInfo, MessageResponse
from app.modules.regulations.service import RegulationService
from app.modules.regulations.schemas import (
    RegulationUploadRequest,
    RegulationUpdateRequest,
    RegulationResponse,
    RegulationDetailResponse,
    RegulationListParams,
    RegulationContent,
)
from app.i18n import t
from app.utils.response import ApiResponse, PaginatedResponse, success_response, paginated_response

router = APIRouter(prefix="/regulations", tags=["法規管理"])


def _is_admin(user: UserInfo) -> bool:
    """檢查使用者是否為管理員"""
    return user.is_superuser or "admin" in user.roles


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[RegulationResponse]],
    summary="獲取法規列表",
    description="獲取法規列表(支援分頁與篩選)，管理員可查看所有資料，一般使用者只能查看自己的資料"
)
async def get_regulations(
    page: int = Query(default=1, ge=1, description="頁碼(從 1 開始)"),
    page_size: int = Query(default=20, ge=1, le=100, description="每頁筆數(1-100)"),
    law_name: str | None = Query(default=None, description="法規名稱(模糊搜尋)"),
    category: str | None = Query(default=None, description="法規類別(精確搜尋)"),
    status_filter: str | None = Query(default=None, alias="status", description="法規狀態(精確搜尋)"),
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取法規列表

    權限要求:
    - 需要登入
    - 管理員可查看所有資料
    - 一般使用者只能查看自己的資料

    查詢參數:
    - page: 頁碼(從 1 開始)
    - page_size: 每頁筆數(1-100)
    - law_name: 法規名稱(模糊搜尋)
    - category: 法規類別(精確搜尋)
    - status: 法規狀態(精確搜尋)

    回應:
    - 法規列表與分頁資訊（包含計算的統計資料）
    """
    params = RegulationListParams(
        page=page,
        page_size=page_size,
        law_name=law_name,
        category=category,
        status=status_filter,
    )

    service = RegulationService(db)
    is_admin = _is_admin(current_user)
    regulations, total = await service.get_regulations(
        params,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 使用 from_orm_with_stats 類方法轉換並計算統計資料
    regulation_list = [
        RegulationResponse.from_orm_with_stats(regulation)
        for regulation in regulations
    ]

    return paginated_response(
        items=regulation_list,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/{regulation_id}",
    response_model=ApiResponse[RegulationDetailResponse],
    summary="獲取單一法規詳情",
    description="根據 ID 獲取法規詳細資訊（包含完整內容），管理員可查看所有資料，一般使用者只能查看自己的資料"
)
async def get_regulation(
    regulation_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取單一法規詳情

    權限要求:
    - 需要登入
    - 管理員可查看所有資料
    - 一般使用者只能查看自己的資料

    路徑參數:
    - regulation_id: 法規 ID

    回應:
    - 法規詳細資訊（包含完整 content）
    """
    service = RegulationService(db)
    is_admin = _is_admin(current_user)
    regulation = await service.get_regulation_by_id(
        regulation_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 使用 from_orm_with_stats 方法創建響應（包含統計資料）
    regulation_response = RegulationDetailResponse.from_orm_with_stats(regulation)

    return success_response(data=regulation_response)


@router.post(
    "",
    response_model=ApiResponse[RegulationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="上傳法規",
    description="上傳新法規資料"
)
async def create_regulation(
    request: RegulationUploadRequest,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    上傳新法規

    權限要求:
    - 需要登入

    請求體:
    - content: 完整法規內容（JSON格式）
      - law_metadata: 法規基本資料
      - chapters: 章節列表

    回應:
    - 新建立的法規資訊（包含計算的統計資料）
    """
    service = RegulationService(db)
    new_regulation = await service.create_regulation(request, current_user.id)

    # 使用 from_orm_with_stats 計算統計資料
    regulation_response = RegulationResponse.from_orm_with_stats(new_regulation)

    return success_response(
        data=regulation_response,
        message=t('regulations.uploadSuccess')
    )


@router.put(
    "/{regulation_id}",
    response_model=ApiResponse[RegulationResponse],
    summary="更新法規",
    description="更新法規資訊（主要更新 scenarios），管理員可更新所有資料，一般使用者只能更新自己的資料"
)
async def update_regulation(
    regulation_id: int,
    request: RegulationUpdateRequest,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    更新法規資訊

    權限要求:
    - 需要登入
    - 管理員可更新所有資料
    - 一般使用者只能更新自己的資料

    路徑參數:
    - regulation_id: 法規 ID

    請求體:
    - content: 完整法規內容（包含更新後的 scenarios）

    回應:
    - 更新後的法規資訊（包含計算的統計資料）
    """
    service = RegulationService(db)
    is_admin = _is_admin(current_user)
    updated_regulation = await service.update_regulation(
        regulation_id,
        request,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 使用 from_orm_with_stats 計算統計資料
    regulation_response = RegulationResponse.from_orm_with_stats(updated_regulation)

    return success_response(
        data=regulation_response,
        message=t('regulations.updateSuccess')
    )


@router.delete(
    "/{regulation_id}",
    response_model=ApiResponse[MessageResponse],
    summary="刪除法規",
    description="刪除法規，管理員可刪除所有資料，一般使用者只能刪除自己的資料"
)
async def delete_regulation(
    regulation_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    刪除法規

    權限要求:
    - 需要登入
    - 管理員可刪除所有資料
    - 一般使用者只能刪除自己的資料

    路徑參數:
    - regulation_id: 法規 ID

    回應:
    - 刪除成功訊息
    """
    service = RegulationService(db)
    is_admin = _is_admin(current_user)
    await service.delete_regulation(
        regulation_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    return success_response(
        data=MessageResponse(message=t('regulations.deleteSuccess')),
        message=t('regulations.deleteSuccess')
    )


@router.get(
    "/{regulation_id}/export",
    summary="導出法規為 JSON",
    description="導出法規為 JSON 格式文件，管理員可導出所有資料，一般使用者只能導出自己的資料"
)
async def export_regulation(
    regulation_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    導出法規為 JSON 格式文件

    權限要求:
    - 需要登入
    - 管理員可導出所有資料
    - 一般使用者只能導出自己的資料

    路徑參數:
    - regulation_id: 法規 ID

    回應:
    - JSON 文件下載（Content-Type: application/json）
    """
    logger.info(
        f"User {current_user.username} (ID: {current_user.id}) "
        f"exporting regulation {regulation_id}"
    )

    service = RegulationService(db)
    is_admin = _is_admin(current_user)

    # 獲取法規數據
    content = await service.export_regulation_json(
        regulation_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 獲取法規名稱用於文件名
    regulation = await service.get_regulation_by_id(
        regulation_id,
        user_id=current_user.id,
        is_admin=is_admin
    )
    law_name = regulation.law_name
    filename = f"{law_name}.json"

    # 將 JSON 轉換為字節流
    json_bytes = json.dumps(content, ensure_ascii=False, indent=2).encode('utf-8')
    file_stream = BytesIO(json_bytes)

    # 對文件名進行 URL 編碼以支持中文
    # RFC 5987: filename*=UTF-8''encoded_filename
    encoded_filename = quote(filename)

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Content-Type": "application/json; charset=utf-8"
    }

    logger.success(f"Regulation {regulation_id} exported successfully")

    return StreamingResponse(
        file_stream,
        media_type="application/json",
        headers=headers
    )
