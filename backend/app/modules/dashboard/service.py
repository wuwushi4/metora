# -*- coding: utf-8 -*-
"""
Dashboard 服務: 提供儀表板統計查詢
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, cast, desc
from sqlalchemy.dialects.postgresql import JSONB, JSON
from loguru import logger

from app.db.models.chat_session import ChatSession
from app.db.models.chat_message import ChatMessage
from app.db.models.message_feedback import MessageFeedback, FeedbackType
from app.db.models.expert_review import ExpertReview
from app.modules.dashboard.schemas import (
    AdminDashboardStats,
    ChatStats,
    FeedbackStats,
    IssueTagCount,
    UserDashboardInfo,
    BasicStats,
    TimeRange,
)


class DashboardService:
    """儀表板服務"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_date_range(self, time_range: TimeRange) -> Tuple[Optional[datetime], datetime]:
        """
        計算時間範圍的起始和結束時間

        Args:
            time_range: 時間範圍枚舉

        Returns:
            (start_date, end_date): 起始和結束時間元組
        """
        now = datetime.now(timezone.utc)

        if time_range == TimeRange.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == TimeRange.THIS_WEEK:
            # 本週一作為起始日
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == TimeRange.THIS_MONTH:
            # 本月 1 日作為起始日
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_range == TimeRange.LAST_7_DAYS:
            start = now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            start = now - timedelta(days=30)
        else:  # TimeRange.ALL
            start = None

        return (start, now)

    async def _get_chat_stats(
        self,
        start_date: Optional[datetime],
        end_date: datetime
    ) -> ChatStats:
        """
        獲取聊天互動統計

        Args:
            start_date: 起始時間 (None 表示全部)
            end_date: 結束時間

        Returns:
            ChatStats: 聊天統計數據
        """
        # 1. 總對話數
        query = select(func.count(ChatSession.id)).where(ChatSession.is_active == True)
        if start_date:
            query = query.where(ChatSession.created_at >= start_date)
        total_sessions = await self.db.scalar(query) or 0

        # 2. 總訊息數
        query = select(func.count(ChatMessage.id))
        if start_date:
            query = query.where(ChatMessage.created_at >= start_date)
        total_messages = await self.db.scalar(query) or 0

        # 3. 日均訊息量 (僅當有時間範圍時計算)
        if start_date:
            days = (end_date - start_date).days + 1
            daily_avg = round(total_messages / days, 2) if days > 0 else 0.0
        else:
            daily_avg = 0.0

        # 4. Graph 類型分布
        query = select(
            ChatSession.graph_type,
            func.count(ChatSession.id).label('count')
        ).where(ChatSession.is_active == True)
        if start_date:
            query = query.where(ChatSession.created_at >= start_date)
        query = query.group_by(ChatSession.graph_type)

        results = await self.db.execute(query)
        graph_distribution = {row.graph_type: row.count for row in results}

        return ChatStats(
            total_sessions=total_sessions,
            total_messages=total_messages,
            daily_avg_messages=daily_avg,
            graph_type_distribution=graph_distribution
        )

    async def _get_feedback_stats(
        self,
        start_date: Optional[datetime],
        total_messages: int
    ) -> FeedbackStats:
        """
        獲取 AI 品質反饋統計

        Args:
            start_date: 起始時間 (None 表示全部)
            total_messages: 總訊息數 (用於計算反饋率)

        Returns:
            FeedbackStats: 反饋統計數據
        """
        # 1. 讚踩統計
        query = select(
            func.count(MessageFeedback.id).label('total'),
            func.sum(
                case((MessageFeedback.feedback_type == FeedbackType.THUMBS_UP, 1), else_=0)
            ).label('thumbs_up'),
            func.sum(
                case((MessageFeedback.feedback_type == FeedbackType.THUMBS_DOWN, 1), else_=0)
            ).label('thumbs_down')
        )
        if start_date:
            query = query.where(MessageFeedback.created_at >= start_date)

        result = await self.db.execute(query)
        row = result.one()

        total_feedbacks = row.total or 0
        thumbs_up_count = row.thumbs_up or 0
        thumbs_down_count = row.thumbs_down or 0

        # 2. 反饋率 (有反饋的訊息 / 總訊息數)
        feedback_rate = round((total_feedbacks / total_messages * 100), 2) if total_messages > 0 else 0.0

        # 3. 讚比例
        thumbs_up_rate = round((thumbs_up_count / total_feedbacks * 100), 2) if total_feedbacks > 0 else 0.0

        # 4. 待審查反饋數 (thumbs_down 且未關聯 ExpertReview)
        query = select(func.count(MessageFeedback.id)).outerjoin(
            ExpertReview,
            MessageFeedback.id == ExpertReview.feedback_id
        ).where(
            and_(
                MessageFeedback.feedback_type == FeedbackType.THUMBS_DOWN,
                ExpertReview.id.is_(None)
            )
        )
        if start_date:
            query = query.where(MessageFeedback.created_at >= start_date)

        pending_count = await self.db.scalar(query) or 0

        # 5. 常見問題標籤 Top 10 (使用 PostgreSQL json_array_elements_text)
        # 注意: json_array_elements_text 在空陣列時不會返回任何行，所以不需要檢查空陣列
        query = select(
            func.json_array_elements_text(MessageFeedback.issue_tags).label('tag'),
            func.count().label('count')
        ).where(
            MessageFeedback.issue_tags.isnot(None)
        )
        if start_date:
            query = query.where(MessageFeedback.created_at >= start_date)
        query = query.group_by('tag').order_by(desc('count')).limit(10)

        results = await self.db.execute(query)
        top_tags = [IssueTagCount(tag=row.tag, count=row.count) for row in results]

        return FeedbackStats(
            total_feedbacks=total_feedbacks,
            thumbs_up_count=thumbs_up_count,
            thumbs_down_count=thumbs_down_count,
            thumbs_up_rate=thumbs_up_rate,
            feedback_rate=feedback_rate,
            pending_review_count=pending_count,
            top_issue_tags=top_tags
        )

    async def get_admin_stats(
        self,
        time_range: TimeRange = TimeRange.ALL
    ) -> AdminDashboardStats:
        """
        獲取 Admin 儀表板統計數據

        Args:
            time_range: 時間範圍

        Returns:
            AdminDashboardStats: Admin 儀表板統計
        """
        logger.info(f"獲取 Admin 儀表板統計, 時間範圍: {time_range.value}")

        # 計算時間範圍
        start_date, end_date = self._get_date_range(time_range)

        # 獲取聊天統計
        chat_stats = await self._get_chat_stats(start_date, end_date)

        # 獲取反饋統計 (需要 total_messages 計算反饋率)
        feedback_stats = await self._get_feedback_stats(start_date, chat_stats.total_messages)

        logger.info(
            f"Admin 統計完成 - 對話數: {chat_stats.total_sessions}, "
            f"訊息數: {chat_stats.total_messages}, "
            f"反饋數: {feedback_stats.total_feedbacks}"
        )

        return AdminDashboardStats(
            time_range=time_range.value,
            period_start=start_date,
            period_end=end_date,
            chat_stats=chat_stats,
            feedback_stats=feedback_stats
        )

    async def get_user_info(self, user_id: int, username: str) -> UserDashboardInfo:
        """
        獲取 User 儀表板資訊

        Args:
            user_id: 使用者 ID
            username: 使用者名稱

        Returns:
            UserDashboardInfo: User 儀表板資訊
        """
        logger.info(f"獲取 User 儀表板資訊, 使用者 ID: {user_id}")

        # 查詢個人對話數
        query = select(func.count(ChatSession.id)).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            )
        )
        total_sessions = await self.db.scalar(query) or 0

        # 查詢個人訊息數 (透過 ChatSession 關聯)
        query = select(func.count(ChatMessage.id)).join(
            ChatSession,
            ChatMessage.session_id == ChatSession.id
        ).where(ChatSession.user_id == user_id)
        total_messages = await self.db.scalar(query) or 0

        logger.info(
            f"User 統計完成 - 對話數: {total_sessions}, 訊息數: {total_messages}"
        )

        return UserDashboardInfo(
            username=username,
            welcome_message=f"歡迎回來, {username}! 👋",
            basic_stats=BasicStats(
                total_sessions=total_sessions,
                total_messages=total_messages
            )
        )
