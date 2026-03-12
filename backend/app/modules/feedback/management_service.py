# -*- coding: utf-8 -*-
"""
反饋管理服務 (管理員功能)

提供反饋記錄的查詢、詳情和專家審查功能
"""
from typing import Optional, Tuple, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from app.db.models.message_feedback import MessageFeedback, FeedbackType
from app.db.models.expert_review import ExpertReview
from app.db.models.chat_message import ChatMessage
from app.db.models.chat_session import ChatSession
from app.db.models.collection import Collection
from app.db.models.user import User
from app.modules.feedback.schemas import (
    ExpertReviewRequest,
    ExpertReviewResponse,
    FeedbackDetailResponse,
    FeedbackListItem,
    MessageWithMetadata,
    UserBasicInfo,
)
from app.utils.exceptions import ResourceNotFoundError, ValidationError


class FeedbackManagementService:
    """反饋管理服務 (管理員功能)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_feedbacks_list(
        self,
        page: int = 1,
        page_size: int = 20,
        feedback_type: Optional[FeedbackType] = None,
        is_reviewed: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        graph_type: Optional[str] = None,
        collection_id: Optional[int] = None
    ) -> Tuple[List[FeedbackListItem], int]:
        """
        取得反饋列表 (支援分頁與篩選)

        使用 selectinload 避免 N+1 查詢問題
        """
        # 建立基本查詢
        stmt = (
            select(MessageFeedback)
            .options(
                selectinload(MessageFeedback.user),  # 預載入使用者
                selectinload(MessageFeedback.message).selectinload(ChatMessage.session),  # 預載入訊息和 Session
                selectinload(MessageFeedback.expert_review)  # 預載入審查記錄
                    .selectinload(ExpertReview.reviewer)  # 預載入審查者
            )
        )

        # 篩選條件
        filters = []

        # feedback_type 篩選
        if feedback_type:
            filters.append(MessageFeedback.feedback_type == feedback_type)

        # is_reviewed 篩選 (關聯是否存在)
        if is_reviewed is not None:
            if is_reviewed:
                # 已審查: expert_review 存在
                stmt = stmt.join(MessageFeedback.expert_review)
            else:
                # 未審查: expert_review 不存在
                stmt = stmt.outerjoin(MessageFeedback.expert_review).filter(
                    ExpertReview.id.is_(None)
                )

        # 日期範圍篩選
        if start_date:
            filters.append(MessageFeedback.created_at >= start_date)
        if end_date:
            filters.append(MessageFeedback.created_at <= end_date)

        # graph_type 或 collection_id 篩選 (需要 JOIN ChatSession)
        has_joined_session = False
        if graph_type or collection_id:
            stmt = stmt.join(MessageFeedback.message).join(ChatMessage.session)
            has_joined_session = True

            if graph_type:
                filters.append(ChatSession.graph_type == graph_type)

            if collection_id:
                from sqlalchemy.dialects.postgresql import JSONB
                from sqlalchemy import cast
                # 將 JSON 轉為 JSONB 並使用 @> 操作符檢查是否包含該 ID
                filters.append(
                    cast(ChatSession.collection_ids, JSONB).contains([collection_id])
                )

        # 套用篩選條件
        if filters:
            stmt = stmt.filter(and_(*filters))

        # 計算總筆數
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 排序與分頁
        stmt = stmt.order_by(desc(MessageFeedback.created_at))
        stmt = stmt.limit(page_size).offset((page - 1) * page_size)

        # 執行查詢
        result = await self.db.execute(stmt)
        feedbacks = result.scalars().all()

        # ========================================
        # 批量查詢 Collections（消除 N+1 問題）
        # ========================================
        # 1. 收集所有需要的 collection_ids
        all_collection_ids = set()
        for feedback in feedbacks:
            session = feedback.message.session
            if session and session.collection_ids:
                all_collection_ids.update(session.collection_ids)

        # 2. 一次性批量查詢所有 Collections
        collection_map = {}  # {id: Collection}
        if all_collection_ids:
            coll_stmt = select(Collection).filter(Collection.id.in_(all_collection_ids))
            coll_result = await self.db.execute(coll_stmt)
            collections = coll_result.scalars().all()
            collection_map = {c.id: c for c in collections}

        # 3. 轉換為回應模型（從記憶體映射中查詢，無需額外 SQL）
        items = []
        for feedback in feedbacks:
            # 獲取 Session 資訊
            session = feedback.message.session
            graph_type = session.graph_type if session else "base_graph"
            collection_ids = session.collection_ids if session else []

            # 從記憶體映射中取得 Collection 名稱（無 SQL 查詢！）
            collection_names = [
                collection_map[cid].name
                for cid in collection_ids
                if cid in collection_map
            ]

            items.append(FeedbackListItem(
                id=feedback.id,
                message_id=feedback.message_id,
                user=UserBasicInfo.model_validate(feedback.user),
                message_preview=feedback.message.content[:100],  # 前 100 字
                feedback_type=feedback.feedback_type,
                issue_tags=feedback.issue_tags,
                is_reviewed=feedback.expert_review is not None,
                is_interrupted=feedback.message.extra_data.get('interrupted', False),
                created_at=feedback.created_at,
                # 新增欄位
                graph_type=graph_type,
                collection_ids=collection_ids,
                collection_names=collection_names
            ))

        logger.info(
            f"查詢反饋列表: page={page}, total={total}, "
            f"collections_batch_query=1 (optimized from N+1)"
        )

        return items, total

    async def get_feedback_detail(
        self,
        feedback_id: UUID
    ) -> FeedbackDetailResponse:
        """
        取得反饋詳情

        包含:
        1. 反饋基本資訊
        2. 關聯的訊息與元資料
        3. 使用者提問 (前一則 user 訊息)
        4. 專家審查記錄 (如果存在)
        """
        # 查詢反饋 (預載入關聯)
        stmt = (
            select(MessageFeedback)
            .options(
                selectinload(MessageFeedback.user),
                selectinload(MessageFeedback.message).selectinload(ChatMessage.attachments),
                selectinload(MessageFeedback.message).selectinload(ChatMessage.session),  # 預載入 Session
                selectinload(MessageFeedback.expert_review)
                    .selectinload(ExpertReview.reviewer)
            )
            .filter(MessageFeedback.id == feedback_id)
        )

        result = await self.db.execute(stmt)
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise ResourceNotFoundError(f"反饋 {feedback_id} 不存在")

        # 查詢使用者提問 (前一則 user 訊息) - 完整物件
        user_message = None
        user_question = None  # 保留字串用於向後相容

        prev_message_stmt = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.attachments))
            .filter(
                and_(
                    ChatMessage.session_id == feedback.message.session_id,
                    ChatMessage.role == "user",
                    ChatMessage.created_at < feedback.message.created_at
                )
            )
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        prev_result = await self.db.execute(prev_message_stmt)
        user_message_obj = prev_result.scalar_one_or_none()

        if user_message_obj:
            user_question = user_message_obj.content  # 字串
            user_message = MessageWithMetadata.model_validate(user_message_obj)  # 完整物件

        # 獲取 Session 資訊
        session = feedback.message.session
        graph_type = session.graph_type if session else "base_graph"
        collection_ids = session.collection_ids if session else []

        # 查詢 Collection 名稱
        collection_names = []
        if collection_ids:
            coll_stmt = select(Collection).filter(Collection.id.in_(collection_ids))
            coll_result = await self.db.execute(coll_stmt)
            collections = coll_result.scalars().all()
            collection_names = [c.name for c in collections]

        # 組裝回應
        detail = FeedbackDetailResponse(
            id=feedback.id,
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            user=UserBasicInfo.model_validate(feedback.user),
            feedback_type=feedback.feedback_type,
            issue_tags=feedback.issue_tags,
            comment=feedback.comment,
            created_at=feedback.created_at,
            message=MessageWithMetadata.model_validate(feedback.message),
            user_question=user_question,
            user_message=user_message,
            expert_review=(
                ExpertReviewResponse.model_validate(feedback.expert_review)
                if feedback.expert_review else None
            ),
            # 新增欄位
            graph_type=graph_type,
            collection_ids=collection_ids,
            collection_names=collection_names
        )

        return detail

    async def submit_expert_review(
        self,
        feedback_id: UUID,
        review_data: ExpertReviewRequest,
        reviewer_id: int
    ) -> ExpertReviewResponse:
        """
        提交或更新專家審查

        業務規則:
        1. 只能對 thumbs_down 類型的反饋進行審查
        2. 支援 UPSERT: 存在則更新,不存在則新增
        """
        # 查詢反饋
        stmt = select(MessageFeedback).options(
            selectinload(MessageFeedback.expert_review)
        ).filter(MessageFeedback.id == feedback_id)

        result = await self.db.execute(stmt)
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise ResourceNotFoundError(f"反饋 {feedback_id} 不存在")

        # 驗證反饋類型
        if feedback.feedback_type != FeedbackType.THUMBS_DOWN:
            raise ValidationError("只能對負面反饋 (thumbs_down) 進行專家審查")

        # UPSERT 邏輯
        if feedback.expert_review:
            # 更新現有審查
            review = feedback.expert_review
            review.expert_opinion = review_data.expert_opinion
            review.suggested_response = review_data.suggested_response
            review.reviewed_by = reviewer_id
            review.updated_at = datetime.utcnow()

            logger.info(f"使用者 {reviewer_id} 更新了反饋 {feedback_id} 的審查")
        else:
            # 建立新審查
            review = ExpertReview(
                feedback_id=feedback_id,
                expert_opinion=review_data.expert_opinion,
                suggested_response=review_data.suggested_response,
                reviewed_by=reviewer_id
            )
            self.db.add(review)

            logger.info(f"使用者 {reviewer_id} 對反饋 {feedback_id} 提交了審查")

        await self.db.commit()
        await self.db.refresh(review)

        # 載入審查者資訊
        await self.db.refresh(review, ["reviewer"])

        response = ExpertReviewResponse.model_validate(review)
        return response
