# -*- coding: utf-8 -*-
"""
統一響應格式
提供標準的 API 響應結構
"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field, ConfigDict
from math import ceil

from app.i18n import t

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    統一 API 響應格式

    提供一致的響應結構，包含成功狀態、資料、訊息

    Note:
        - 成功響應：使用 `success_response()` 輔助函數建立
        - 錯誤響應：由全局異常處理器自動處理（app/core/exception_handlers.py）

    Examples:
        成功響應（使用輔助函數）:
        ```python
        return success_response(
            data={"id": 1, "name": "John"},
            message="獲取成功"
        )
        ```

        錯誤響應（拋出異常，由異常處理器自動處理）:
        ```python
        # Service 層拋出異常
        raise ResourceNotFoundError("使用者", user_id)

        # 異常處理器自動轉換為以下格式：
        # {
        #     "success": false,
        #     "message": "使用者 (ID: 123) 不存在",
        #     "code": "RESOURCE_NOT_FOUND"
        # }
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = Field(..., description="請求是否成功")
    data: Optional[T] = Field(None, description="響應資料")
    message: Optional[str] = Field(None, description="響應訊息")
    code: str = Field(default="SUCCESS", description="狀態碼（用於前端識別）")


# 輔助函數：建立成功響應
def success_response(
    data: Any = None,
    message: str = None,
    code: str = "SUCCESS"
) -> ApiResponse:
    """
    建立成功響應

    Args:
        data: 響應資料
        message: 成功訊息
        code: 狀態碼

    Returns:
        成功的 ApiResponse 實例

    Examples:
        ```python
        return success_response(
            data=user_data,
            message="獲取成功"
        )
        ```
    """
    return ApiResponse(
        success=True,
        data=data,
        message=message if message is not None else t('common.fetchSuccess'),
        code=code
    )


class PaginationMeta(BaseModel):
    """
    分頁元資訊

    包含分頁相關的統計資訊
    """

    total: int = Field(..., description="總記錄數", ge=0)
    page: int = Field(..., description="當前頁碼", ge=1)
    page_size: int = Field(..., description="每頁記錄數", ge=1)
    total_pages: int = Field(..., description="總頁數", ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分頁響應格式

    用於返回分頁資料

    Examples:
        ```python
        return PaginatedResponse(
            items=[user1, user2, user3],
            pagination=PaginationMeta(...)
        )
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: List[T] = Field(..., description="資料列表")
    pagination: PaginationMeta = Field(..., description="分頁資訊")


# 輔助函數：建立分頁響應
def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = None
) -> ApiResponse[PaginatedResponse]:
    """
    建立分頁響應

    Args:
        items: 資料列表
        total: 總記錄數
        page: 當前頁碼
        page_size: 每頁記錄數
        message: 成功訊息

    Returns:
        包含分頁資料的 ApiResponse 實例
    """
    total_pages = ceil(total / page_size) if page_size > 0 else 0

    pagination = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

    paginated_data = PaginatedResponse(
        items=items,
        pagination=pagination
    )

    return ApiResponse(
        success=True,
        data=paginated_data,
        message=message if message is not None else t('common.fetchSuccess'),
        code="SUCCESS"
    )
