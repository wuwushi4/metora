# -*- coding: utf-8 -*-
"""
Dataset 管理 API 路由
提供 Dataset CRUD 和檔案上傳的 RESTful API 端點
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.config import settings
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import UserInfo, MessageResponse
from app.modules.datasets.service import DatasetService
from app.modules.datasets.schemas import (
    ChunkingDefaultsResponse,
    DatasetResponse,
    DatasetListParams,
    UploadResponse,
)
from app.modules.settings.manager import settings_manager
from app.utils.response import ApiResponse, PaginatedResponse, success_response, paginated_response

router = APIRouter(prefix="/datasets", tags=["資料集管理"])


def _is_admin(user: UserInfo) -> bool:
    """檢查使用者是否為管理員"""
    return user.is_superuser or "admin" in user.roles


@router.get(
    "/chunking-defaults",
    response_model=ApiResponse[ChunkingDefaultsResponse],
    summary="取得遞迴分塊預設參數",
    description="取得目前有效的遞迴文字分塊預設參數（系統設定 > 環境變數）"
)
async def get_chunking_defaults(
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
):
    """
    取得遞迴分塊預設參數

    優先級：系統設定 (Settings UI) > 環境變數 (.env)

    權限要求:
    - 需要登入
    """
    chunk_size = (
        settings_manager.get("RECURSIVE_TEXT_CHUNK_SIZE")
        or settings.RECURSIVE_TEXT_CHUNK_SIZE
    )
    chunk_overlap = (
        settings_manager.get("RECURSIVE_TEXT_CHUNK_OVERLAP")
        or settings.RECURSIVE_TEXT_CHUNK_OVERLAP
    )

    return success_response(
        data=ChunkingDefaultsResponse(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedResponse[DatasetResponse]],
    summary="獲取 Dataset 列表",
    description="獲取 Dataset 列表(支援分頁與篩選)，管理員可查看所有資料，一般使用者只能查看自己的資料"
)
async def get_datasets(
    page: int = Query(default=1, ge=1, description="頁碼(從 1 開始)"),
    page_size: int = Query(default=20, ge=1, le=100, description="每頁筆數(1-100)"),
    collection_id: int | None = Query(default=None, description="所屬集合ID(精確搜尋)"),
    vectorized: bool | None = Query(default=None, description="是否已向量化(精確搜尋)"),
    original_filename: str | None = Query(default=None, description="原始檔名(模糊搜尋)"),
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取 Dataset 列表

    權限要求:
    - 需要登入
    - 管理員可查看所有資料
    - 一般使用者只能查看自己的資料

    查詢參數:
    - page: 頁碼(從 1 開始)
    - page_size: 每頁筆數(1-100)
    - collection_id: 所屬集合ID(精確搜尋)
    - vectorized: 是否已向量化(精確搜尋)
    - original_filename: 原始檔名(模糊搜尋)

    回應:
    - Dataset 列表與分頁資訊
    """
    params = DatasetListParams(
        page=page,
        page_size=page_size,
        collection_id=collection_id,
        vectorized=vectorized,
        original_filename=original_filename,
    )

    service = DatasetService(db)
    is_admin = _is_admin(current_user)
    datasets, total = await service.get_datasets(
        params,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 將 ORM 物件轉換為 Response Schema
    dataset_list = [
        DatasetResponse(
            id=dataset.id,
            collection_id=dataset.collection_id,
            filename=dataset.filename,
            original_filename=dataset.original_filename,
            file_path=dataset.file_path,
            file_size=dataset.file_size,
            file_type=dataset.file_type,
            chunk_count=dataset.chunk_count,
            vectorized=dataset.vectorized,
            vectorization_error=dataset.vectorization_error,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )
        for dataset in datasets
    ]

    return paginated_response(
        items=dataset_list,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get(
    "/{dataset_id}",
    response_model=ApiResponse[DatasetResponse],
    summary="獲取單一 Dataset",
    description="根據 ID 獲取 Dataset 詳細資訊，管理員可查看所有資料，一般使用者只能查看自己的資料"
)
async def get_dataset(
    dataset_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    獲取單一 Dataset

    權限要求:
    - 需要登入
    - 管理員可查看所有資料
    - 一般使用者只能查看自己的資料

    路徑參數:
    - dataset_id: Dataset ID

    回應:
    - Dataset 詳細資訊
    """
    service = DatasetService(db)
    is_admin = _is_admin(current_user)
    dataset = await service.get_dataset_by_id(
        dataset_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    dataset_response = DatasetResponse(
        id=dataset.id,
        collection_id=dataset.collection_id,
        filename=dataset.filename,
        original_filename=dataset.original_filename,
        file_path=dataset.file_path,
        file_size=dataset.file_size,
        file_type=dataset.file_type,
        chunk_count=dataset.chunk_count,
        vectorized=dataset.vectorized,
        vectorization_error=dataset.vectorization_error,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )

    return success_response(data=dataset_response)


@router.post(
    "/upload",
    response_model=ApiResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="上傳檔案",
    description="上傳檔案到指定 Collection 並自動開始向量化處理"
)
async def upload_dataset(
    collection_id: int = Query(..., description="所屬集合ID"),
    chunk_size: Optional[int] = Query(None, ge=50, le=10000, description="分塊大小（字元數），僅 recursive_text 策略適用"),
    chunk_overlap: Optional[int] = Query(None, ge=0, le=5000, description="重疊大小（字元數），僅 recursive_text 策略適用"),
    file: UploadFile = File(..., description="要上傳的檔案"),
    background_tasks: BackgroundTasks = None,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    上傳檔案

    權限要求:
    - 需要登入
    - 管理員可上傳到任何 Collection
    - 一般使用者只能上傳到自己的 Collection

    查詢參數:
    - collection_id: 所屬集合ID
    - chunk_size: 分塊大小（可選，僅 recursive_text 策略適用）
    - chunk_overlap: 重疊大小（可選，僅 recursive_text 策略適用）

    表單數據:
    - file: 要上傳的檔案（支援的格式見環境變數配置）

    回應:
    - 上傳成功的 Dataset 資訊
    - 向量化處理將在背景執行
    """
    service = DatasetService(db)
    is_admin = _is_admin(current_user)

    # 上傳檔案並建立 Dataset
    new_dataset = await service.upload_dataset(
        collection_id=collection_id,
        file=file,
        user_id=current_user.id,
        is_admin=is_admin
    )

    # 將向量化處理加入背景任務（傳入使用者指定的分塊參數）
    background_tasks.add_task(
        service.vectorize_dataset,
        new_dataset.id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    dataset_response = DatasetResponse(
        id=new_dataset.id,
        collection_id=new_dataset.collection_id,
        filename=new_dataset.filename,
        original_filename=new_dataset.original_filename,
        file_path=new_dataset.file_path,
        file_size=new_dataset.file_size,
        file_type=new_dataset.file_type,
        chunk_count=new_dataset.chunk_count,
        vectorized=new_dataset.vectorized,
        vectorization_error=new_dataset.vectorization_error,
        created_at=new_dataset.created_at,
        updated_at=new_dataset.updated_at,
    )

    upload_response = UploadResponse(
        dataset=dataset_response,
        message="檔案上傳成功，向量化處理中..."
    )

    return success_response(
        data=upload_response,
        message="檔案上傳成功"
    )


@router.delete(
    "/{dataset_id}",
    response_model=ApiResponse[MessageResponse],
    summary="刪除 Dataset",
    description="刪除 Dataset（包含檔案和向量資料），管理員可刪除所有資料，一般使用者只能刪除自己的資料"
)
async def delete_dataset(
    dataset_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    刪除 Dataset

    權限要求:
    - 需要登入
    - 管理員可刪除所有資料
    - 一般使用者只能刪除自己的資料

    路徑參數:
    - dataset_id: Dataset ID

    回應:
    - 刪除成功訊息
    """
    service = DatasetService(db)
    is_admin = _is_admin(current_user)
    await service.delete_dataset(
        dataset_id,
        user_id=current_user.id,
        is_admin=is_admin
    )

    return success_response(
        data=MessageResponse(message="資料集刪除成功"),
        message="資料集刪除成功"
    )
