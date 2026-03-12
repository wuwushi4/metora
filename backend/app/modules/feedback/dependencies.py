# -*- coding: utf-8 -*-
"""
反饋模組依賴注入
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.feedback.service import FeedbackService
from app.modules.feedback.management_service import FeedbackManagementService


def get_feedback_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FeedbackService:
    """注入 FeedbackService"""
    return FeedbackService(db=db)


def get_feedback_management_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FeedbackManagementService:
    """注入 FeedbackManagementService"""
    return FeedbackManagementService(db=db)


# 類型別名,方便在 router 中使用
FeedbackServiceDep = Annotated[FeedbackService, Depends(get_feedback_service)]
FeedbackManagementServiceDep = Annotated[FeedbackManagementService, Depends(get_feedback_management_service)]
