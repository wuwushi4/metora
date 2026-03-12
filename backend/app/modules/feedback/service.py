# -*- coding: utf-8 -*-
"""
反饋服務: 管理使用者對訊息的反饋
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from loguru import logger

from app.db.models.message_feedback import MessageFeedback, FeedbackType
from app.db.models.chat_message import ChatMessage
from app.modules.feedback.schemas import (
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
)
from app.utils.response import success_response, ApiResponse
from app.utils.exceptions import ResourceNotFoundError, ValidationError, AuthorizationError


class FeedbackService:
    """反饋服務"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_message_ownership(self, message_id: UUID, user_id: int) -> ChatMessage:
        """
        驗證訊息所有權

        Args:
            message_id: 訊息 ID
            user_id: 使用者 ID

        Returns:
            ChatMessage: 訊息物件

        Raises:
            ResourceNotFoundError: 訊息不存在
            AuthorizationError: 無權限對此訊息反饋
        """
        # 查詢訊息並連接 Session
        stmt = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise ResourceNotFoundError(f"訊息 {message_id} 不存在")

        # 驗證訊息所屬 Session 是否屬於該使用者
        if message.session.user_id != user_id:
            raise AuthorizationError("無權限對此訊息反饋")

        # 驗證訊息是否為助手回應
        if message.role != "assistant":
            raise ValidationError("只能對助手回應進行反饋")

        return message

    async def create_or_update_feedback(
        self,
        user_id: int,
        request: FeedbackCreate
    ) -> ApiResponse[FeedbackResponse]:
        """
        建立或更新反饋 (UPSERT 邏輯)

        Args:
            user_id: 使用者 ID
            request: 反饋建立請求

        Returns:
            ApiResponse[FeedbackResponse]: 反饋回應
        """
        # 驗證訊息所有權
        await self._verify_message_ownership(request.message_id, user_id)

        # 查詢是否已有反饋
        stmt = select(MessageFeedback).where(
            and_(
                MessageFeedback.message_id == request.message_id,
                MessageFeedback.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        existing_feedback = result.scalar_one_or_none()

        if existing_feedback:
            # 更新現有反饋
            existing_feedback.feedback_type = request.feedback_type
            existing_feedback.issue_tags = request.issue_tags
            existing_feedback.comment = request.comment
            existing_feedback.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(existing_feedback)

            logger.info(
                f"使用者 {user_id} 更新了對訊息 {request.message_id} 的反饋: {request.feedback_type}"
            )

            return success_response(
                data=FeedbackResponse.model_validate(existing_feedback),
                message="反饋更新成功"
            )
        else:
            # 建立新反饋
            feedback = MessageFeedback(
                message_id=request.message_id,
                user_id=user_id,
                feedback_type=request.feedback_type,
                issue_tags=request.issue_tags,
                comment=request.comment
            )
            self.db.add(feedback)
            await self.db.commit()
            await self.db.refresh(feedback)

            logger.info(
                f"使用者 {user_id} 對訊息 {request.message_id} 提交反饋: {request.feedback_type}"
            )

            return success_response(
                data=FeedbackResponse.model_validate(feedback),
                message="反饋提交成功"
            )

    async def get_user_feedback_for_message(
        self,
        message_id: UUID,
        user_id: int
    ) -> Optional[FeedbackResponse]:
        """
        取得使用者對特定訊息的反饋

        Args:
            message_id: 訊息 ID
            user_id: 使用者 ID

        Returns:
            Optional[FeedbackResponse]: 反饋回應，若無反饋則返回 None
        """
        # 驗證訊息所有權
        await self._verify_message_ownership(message_id, user_id)

        # 查詢反饋
        stmt = select(MessageFeedback).where(
            and_(
                MessageFeedback.message_id == message_id,
                MessageFeedback.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        feedback = result.scalar_one_or_none()

        if feedback:
            return FeedbackResponse.model_validate(feedback)
        return None

    async def delete_feedback(
        self,
        feedback_id: UUID,
        user_id: int
    ) -> ApiResponse[None]:
        """
        刪除反饋

        Args:
            feedback_id: 反饋 ID
            user_id: 使用者 ID

        Returns:
            ApiResponse[None]: 刪除成功回應

        Raises:
            ResourceNotFoundError: 反饋不存在
            AuthorizationError: 無權限刪除此反饋
        """
        # 查詢反饋
        stmt = select(MessageFeedback).where(MessageFeedback.id == feedback_id)
        result = await self.db.execute(stmt)
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise ResourceNotFoundError(f"反饋 {feedback_id} 不存在")

        # 驗證所有權
        if feedback.user_id != user_id:
            raise AuthorizationError("無權限刪除此反饋")

        # 刪除反饋
        await self.db.delete(feedback)
        await self.db.commit()

        logger.info(f"使用者 {user_id} 刪除了反饋 {feedback_id}")

        return success_response(
            data=None,
            message="反饋刪除成功"
        )
