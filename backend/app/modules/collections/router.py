# -*- coding: utf-8 -*-
"""
Collection 管理 API 路由
提供 Collection CRUD 的 RESTful API 端點
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import UserInfo, MessageResponse
from app.modules.collections.service import CollectionService
from app.modules.collections.schemas import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionListParams,
    OwnerInfo,
)
from app.utils.response import ApiResponse, PaginatedResponse, success_response, paginated_response

router = APIRouter(prefix="/collections", tags=["資料集合管理"])


def _is_admin(user: UserInfo) -> bool:
    """檢查使用者是否為管理員"""
    return user.is_superuser or "admin" in user.roles


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[CollectionResponse]],
    summary="獲取 Collection 列表",
    description="獲取 Collection 列表(支援分頁與篩選)，管理員可查看所有資料，一般使用者只能查看自己的資料"
)
async def get_collections(
    page: int = Query(default=1, ge=1, description="頁碼(從 1 開始)"),
    page_size: int = Query(default=20, ge=1, le=100, description="每頁筆數(1-100)"),
    name: str | None = Query(default=None, description="集合名稱(模糊搜尋)"),
    chunking_strategy: str | None = Query(default=None, description="分塊策略(精確搜尋)"),
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取 Collection 列表

    權限要求:
    - 需要登入
    - 管理員可查看所有資料
    - 一般使用者只能查看自己的資料

    查詢參數:
    - page: 頁碼(從 1 開始)
    - page_size: 每頁筆數(1-100)
    - name: 集合名稱(模糊搜尋)
    - chunking_strategy: 分塊策略(精確搜尋)

    回應:
    - Collection 列表與分頁資訊
    """
    params = CollectionListParams(
        page=page,
        page_size=page_size,
        name=name,
        chunking_strategy=chunking_strategy,
    )

    service = CollectionService(db)
    is_admin = _is_admin(current_user)
    collections, total = await service.get_collections(
        params,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 將 ORM 物件轉換為 Response Schema
    collection_list = [
        CollectionResponse(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            user_id=collection.user_id,
            chunking_strategy=collection.chunking_strategy,
            dataset_count=len(collection.datasets),
            owner=OwnerInfo(
                id=collection.user.id,
                username=collection.user.username,
                full_name=collection.user.full_name
            ) if collection.user else None,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
        for collection in collections
    ]

    return paginated_response(
        items=collection_list,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/{collection_id}",
    response_model=ApiResponse[CollectionResponse],
    summary="獲取單一 Collection",
    description="根據 ID 獲取 Collection 詳細資訊，管理員可查看所有資料，一般使用者只能查看自己的資料"
)
async def get_collection(
    collection_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取單一 Collection

    權限要求:
    - 需要登入
    - 管理員可查看所有資料
    - 一般使用者只能查看自己的資料

    路徑參數:
    - collection_id: Collection ID

    回應:
    - Collection 詳細資訊
    """
    service = CollectionService(db)
    is_admin = _is_admin(current_user)
    collection = await service.get_collection_by_id(
        collection_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    collection_response = CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        user_id=collection.user_id,
        chunking_strategy=collection.chunking_strategy,
        dataset_count=len(collection.datasets),
        owner=OwnerInfo(
            id=collection.user.id,
            username=collection.user.username,
            full_name=collection.user.full_name
        ) if collection.user else None,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )

    return success_response(data=collection_response)


@router.post(
    "",
    response_model=ApiResponse[CollectionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="建立 Collection",
    description="建立新 Collection"
)
async def create_collection(
    request: CollectionCreate,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    建立新 Collection

    權限要求:
    - 需要登入

    請求體:
    - name: 集合名稱(1-100字元)
    - description: 集合描述(可選,最多500字元)
    - chunking_strategy: 分塊策略名稱(預設為 qa_multi_representation)

    回應:
    - 新建立的 Collection 資訊
    """
    service = CollectionService(db)
    new_collection = await service.create_collection(request, current_user.id)

    collection_response = CollectionResponse(
        id=new_collection.id,
        name=new_collection.name,
        description=new_collection.description,
        user_id=new_collection.user_id,
        chunking_strategy=new_collection.chunking_strategy,
        dataset_count=len(new_collection.datasets),
        owner=OwnerInfo(
            id=new_collection.user.id,
            username=new_collection.user.username,
            full_name=new_collection.user.full_name
        ) if new_collection.user else None,
        created_at=new_collection.created_at,
        updated_at=new_collection.updated_at,
    )

    return success_response(
        data=collection_response,
        message="集合建立成功"
    )


@router.put(
    "/{collection_id}",
    response_model=ApiResponse[CollectionResponse],
    summary="更新 Collection",
    description="更新 Collection 資訊，管理員可更新所有資料，一般使用者只能更新自己的資料"
)
async def update_collection(
    collection_id: int,
    request: CollectionUpdate,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    更新 Collection 資訊

    權限要求:
    - 需要登入
    - 管理員可更新所有資料
    - 一般使用者只能更新自己的資料

    路徑參數:
    - collection_id: Collection ID

    請求體:
    - name: 集合名稱(可選)
    - description: 集合描述(可選)

    回應:
    - 更新後的 Collection 資訊
    """
    service = CollectionService(db)
    is_admin = _is_admin(current_user)
    updated_collection = await service.update_collection(
        collection_id,
        request,
        user_id=current_user.id,
        is_admin=is_admin
    )

    collection_response = CollectionResponse(
        id=updated_collection.id,
        name=updated_collection.name,
        description=updated_collection.description,
        user_id=updated_collection.user_id,
        chunking_strategy=updated_collection.chunking_strategy,
        dataset_count=len(updated_collection.datasets),
        owner=OwnerInfo(
            id=updated_collection.user.id,
            username=updated_collection.user.username,
            full_name=updated_collection.user.full_name
        ) if updated_collection.user else None,
        created_at=updated_collection.created_at,
        updated_at=updated_collection.updated_at,
    )

    return success_response(
        data=collection_response,
        message="集合資料更新成功"
    )


@router.delete(
    "/{collection_id}",
    response_model=ApiResponse[MessageResponse],
    summary="刪除 Collection",
    description="刪除 Collection（會級聯刪除相關 Dataset），管理員可刪除所有資料，一般使用者只能刪除自己的資料"
)
async def delete_collection(
    collection_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    刪除 Collection

    權限要求:
    - 需要登入
    - 管理員可刪除所有資料
    - 一般使用者只能刪除自己的資料

    路徑參數:
    - collection_id: Collection ID

    回應:
    - 刪除成功訊息
    """
    service = CollectionService(db)
    is_admin = _is_admin(current_user)
    await service.delete_collection(
        collection_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    return success_response(
        data=MessageResponse(message="集合刪除成功"),
        message="集合刪除成功"
    )
