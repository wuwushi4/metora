# -*- coding: utf-8 -*-
"""
反饋模組的 API 路由
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.modules.auth.dependencies import get_current_active_user, require_admin
from app.modules.auth.schemas import UserInfo
from app.modules.feedback.service import FeedbackService
from app.modules.feedback.dependencies import FeedbackServiceDep, FeedbackManagementServiceDep
from app.modules.feedback.schemas import (
    FeedbackCreate,
    FeedbackResponse,
    IssueTagsResponse,
    FeedbackListItem,
    FeedbackDetailResponse,
    ExpertReviewRequest,
    ExpertReviewResponse,
    FeedbackListParams,
)
from app.i18n import t
from app.utils.response import ApiResponse, PaginatedResponse
from app.core.config import get_settings
from app.db.models.message_feedback import FeedbackType

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post(
    "",
    response_model=ApiResponse[FeedbackResponse],
    status_code=status.HTTP_200_OK,
    summary="提交或更新反饋",
    description="使用者對 AI 助理的回應提交反饋(讚/踩)。若已有反饋則更新,否則建立新反饋。",
)
async def submit_feedback(
    request: FeedbackCreate,
    current_user: UserInfo = Depends(get_current_active_user),
    service: FeedbackServiceDep = None,
) -> ApiResponse[FeedbackResponse]:
    """提交或更新反饋"""
    return await service.create_or_update_feedback(
        user_id=current_user.id,
        request=request
    )


@router.get(
    "/message/{message_id}",
    response_model=Optional[FeedbackResponse],
    status_code=status.HTTP_200_OK,
    summary="取得訊息的反饋",
    description="取得使用者對特定訊息的反饋。若無反饋則返回 null。",
)
async def get_message_feedback(
    message_id: UUID,
    current_user: UserInfo = Depends(get_current_active_user),
    service: FeedbackServiceDep = None,
) -> Optional[FeedbackResponse]:
    """取得訊息的反饋"""
    return await service.get_user_feedback_for_message(
        message_id=message_id,
        user_id=current_user.id
    )


@router.delete(
    "/{feedback_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="刪除反饋",
    description="刪除使用者的反饋。",
)
async def delete_feedback(
    feedback_id: UUID,
    current_user: UserInfo = Depends(get_current_active_user),
    service: FeedbackServiceDep = None,
) -> ApiResponse[None]:
    """刪除反饋"""
    return await service.delete_feedback(
        feedback_id=feedback_id,
        user_id=current_user.id
    )


@router.get(
    "/issue-tags",
    response_model=IssueTagsResponse,
    status_code=status.HTTP_200_OK,
    summary="取得問題標籤列表",
    description="取得系統預設的問題標籤列表,用於前端渲染選項。",
)
async def get_issue_tags(
    settings = Depends(get_settings)
) -> IssueTagsResponse:
    """取得問題標籤列表"""
    return IssueTagsResponse(tags=settings.FEEDBACK_ISSUE_TAGS)


# ==========================================
# 管理端點 (僅管理員可訪問)
# ==========================================

@router.get(
    "/management/list",
    response_model=ApiResponse[PaginatedResponse[FeedbackListItem]],
    status_code=status.HTTP_200_OK,
    summary="取得反饋列表 (管理員)",
    description="管理員查看所有反饋記錄,支援分頁與多維度篩選",
    tags=["Feedback Management"]
)
async def get_feedbacks_list(
    page: int = Query(1, ge=1, description="頁碼 (從 1 開始)"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數 (1-100)"),
    feedback_type: Optional[FeedbackType] = Query(None, description="反饋類型篩選"),
    is_reviewed: Optional[bool] = Query(None, description="是否已審查篩選"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    graph_type: Optional[str] = Query(None, description="Agent 類型篩選 (base_graph | rag_graph | regulation_graph)"),
    collection_id: Optional[int] = Query(None, description="知識庫 ID 篩選"),
    current_user: UserInfo = Depends(require_admin),
    service: FeedbackManagementServiceDep = None
) -> ApiResponse[PaginatedResponse[FeedbackListItem]]:
    """取得反饋列表 (管理員)"""
    items, total = await service.get_feedbacks_list(
        page=page,
        page_size=page_size,
        feedback_type=feedback_type,
        is_reviewed=is_reviewed,
        start_date=start_date,
        end_date=end_date,
        graph_type=graph_type,
        collection_id=collection_id
    )

    from app.utils.response import paginated_response
    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message=t('feedback.querySuccess')
    )


@router.get(
    "/management/{feedback_id}",
    response_model=ApiResponse[FeedbackDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="取得反饋詳情 (管理員)",
    description="查看單筆反饋的完整資訊,包含訊息內容、使用者提問、專家審查等",
    tags=["Feedback Management"]
)
async def get_feedback_detail(
    feedback_id: UUID,
    current_user: UserInfo = Depends(require_admin),
    service: FeedbackManagementServiceDep = None
) -> ApiResponse[FeedbackDetailResponse]:
    """取得反饋詳情 (管理員)"""
    detail = await service.get_feedback_detail(feedback_id)

    from app.utils.response import success_response
    return success_response(data=detail, message=t('feedback.querySuccess'))


@router.post(
    "/management/{feedback_id}/review",
    response_model=ApiResponse[ExpertReviewResponse],
    status_code=status.HTTP_200_OK,
    summary="提交專家審查 (管理員)",
    description="對負面反饋提交專家意見,支援更新已有審查",
    tags=["Feedback Management"]
)
async def submit_expert_review(
    feedback_id: UUID,
    review_data: ExpertReviewRequest,
    current_user: UserInfo = Depends(require_admin),
    service: FeedbackManagementServiceDep = None
) -> ApiResponse[ExpertReviewResponse]:
    """提交或更新專家審查 (管理員)"""
    review = await service.submit_expert_review(
        feedback_id=feedback_id,
        review_data=review_data,
        reviewer_id=current_user.id
    )

    from app.utils.response import success_response
    return success_response(data=review, message=t('feedback.reviewSuccess'))
