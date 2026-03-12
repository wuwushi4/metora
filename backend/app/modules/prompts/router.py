# -*- coding: utf-8 -*-
"""
提示詞模組的 API 路由
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import UserInfo, MessageResponse
from app.modules.prompts.service import PromptTemplateService
from app.modules.prompts.schemas import (
    PromptTemplateCreateRequest,
    PromptTemplateUpdateRequest,
    PromptTemplateResponse
)
from app.utils.response import ApiResponse, PaginatedResponse, success_response, paginated_response
from app.utils.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/prompts", tags=["系統提示詞管理"])


@router.get(
    "/templates",
    response_model=ApiResponse[PaginatedResponse[PromptTemplateResponse]],
    summary="取得提示詞列表",
    description="取得當前使用者的提示詞模板列表（支援分頁）"
)
async def get_prompt_templates(
    page: int = Query(default=1, ge=1, description="頁碼(從 1 開始)"),
    page_size: int = Query(default=100, ge=1, le=100, description="每頁筆數(1-100)"),
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    取得提示詞列表

    權限要求:
    - 需要登入
    - 僅可查看自己的提示詞

    查詢參數:
    - page: 頁碼(從 1 開始)
    - page_size: 每頁筆數(1-100)

    回應:
    - 提示詞列表與分頁資訊
    """
    templates, total = await PromptTemplateService.get_user_templates(
        db=db,
        user_id=current_user.id,
        skip=(page - 1) * page_size,
        limit=page_size,
        active_only=True
    )

    template_list = [PromptTemplateResponse.model_validate(t) for t in templates]

    return paginated_response(
        items=template_list,
        total=total,
        page=page,
        page_size=page_size,
        message="獲取提示詞列表成功"
    )


@router.post(
    "/templates",
    response_model=ApiResponse[PromptTemplateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="建立提示詞",
    description="建立新的提示詞模板"
)
async def create_prompt_template(
    data: PromptTemplateCreateRequest,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    建立提示詞模板

    權限要求:
    - 需要登入

    請求 Body:
    - name: 提示詞名稱（1-100字）
    - content: 提示詞內容（1-5000字）
    - description: 提示詞描述（選填，最多500字）
    - is_favorite: 是否收藏（選填，預設為 false）

    回應:
    - 建立成功的提示詞資料
    """
    template = await PromptTemplateService.create_template(
        db=db,
        user_id=current_user.id,
        data=data
    )

    return success_response(
        data=PromptTemplateResponse.model_validate(template),
        message="建立提示詞成功"
    )


@router.get(
    "/templates/{template_id}",
    response_model=ApiResponse[PromptTemplateResponse],
    summary="取得提示詞詳情",
    description="取得指定提示詞模板的詳細資訊"
)
async def get_prompt_template(
    template_id: UUID,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    取得提示詞詳情

    權限要求:
    - 需要登入
    - 僅可查看自己的提示詞

    路徑參數:
    - template_id: 提示詞 ID

    回應:
    - 提示詞詳細資料
    """
    template = await PromptTemplateService.get_template_by_id(
        db=db,
        template_id=template_id,
        user_id=current_user.id
    )

    if not template:
        raise ResourceNotFoundError("提示詞模板", str(template_id))

    return success_response(
        data=PromptTemplateResponse.model_validate(template),
        message="獲取提示詞成功"
    )


@router.patch(
    "/templates/{template_id}",
    response_model=ApiResponse[PromptTemplateResponse],
    summary="更新提示詞",
    description="更新指定提示詞模板"
)
async def update_prompt_template(
    template_id: UUID,
    data: PromptTemplateUpdateRequest,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    更新提示詞模板

    權限要求:
    - 需要登入
    - 僅可更新自己的提示詞

    路徑參數:
    - template_id: 提示詞 ID

    請求 Body:
    - name: 提示詞名稱（選填）
    - content: 提示詞內容（選填）
    - description: 提示詞描述（選填）

    回應:
    - 更新後的提示詞資料
    """
    template = await PromptTemplateService.update_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
        data=data
    )

    if not template:
        raise ResourceNotFoundError("提示詞模板", str(template_id))

    return success_response(
        data=PromptTemplateResponse.model_validate(template),
        message="更新提示詞成功"
    )


@router.delete(
    "/templates/{template_id}",
    response_model=ApiResponse[MessageResponse],
    summary="刪除提示詞",
    description="刪除指定提示詞模板（軟刪除）"
)
async def delete_prompt_template(
    template_id: UUID,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    刪除提示詞模板

    權限要求:
    - 需要登入
    - 僅可刪除自己的提示詞

    路徑參數:
    - template_id: 提示詞 ID

    回應:
    - 刪除成功訊息
    """
    success = await PromptTemplateService.delete_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id
    )

    if not success:
        raise ResourceNotFoundError("提示詞模板", str(template_id))

    return success_response(
        data=MessageResponse(message="刪除成功"),
        message="刪除提示詞成功"
    )


@router.patch(
    "/templates/{template_id}/toggle-favorite",
    response_model=ApiResponse[PromptTemplateResponse],
    summary="切換收藏狀態",
    description="切換指定提示詞的收藏狀態（收藏 ↔ 取消收藏）"
)
async def toggle_favorite_prompt_template(
    template_id: UUID,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """
    切換收藏狀態

    權限要求:
    - 需要登入
    - 僅可切換自己的提示詞收藏狀態

    路徑參數:
    - template_id: 提示詞 ID

    回應:
    - 更新後的提示詞資料

    說明:
    - 如果目前是收藏狀態，則取消收藏
    - 如果目前不是收藏狀態，則設為收藏
    - 允許同時收藏多個提示詞
    """
    template = await PromptTemplateService.toggle_favorite(
        db=db,
        template_id=template_id,
        user_id=current_user.id
    )

    if not template:
        raise ResourceNotFoundError("提示詞模板", str(template_id))

    action = "收藏" if template.is_favorite else "取消收藏"
    return success_response(
        data=PromptTemplateResponse.model_validate(template),
        message=f"{action}提示詞成功"
    )
