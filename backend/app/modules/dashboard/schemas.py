# -*- coding: utf-8 -*-
"""
Dashboard Pydantic 模型
"""
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum


# ==========================================
# 時間範圍枚舉
# ==========================================

class TimeRange(str, Enum):
    """時間範圍枚舉"""
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    ALL = "all"


# ==========================================
# 聊天統計模型
# ==========================================

class ChatStats(BaseModel):
    """聊天互動統計"""
    total_sessions: int = Field(..., description="總對話數")
    total_messages: int = Field(..., description="總訊息數")
    daily_avg_messages: float = Field(..., description="日均訊息量")
    graph_type_distribution: Dict[str, int] = Field(..., description="Graph 類型分布")

    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 156,
                "total_messages": 1234,
                "daily_avg_messages": 45.2,
                "graph_type_distribution": {
                    "base_graph": 45,
                    "rag_graph": 89,
                    "deep_research": 22
                }
            }
        }


# ==========================================
# 反饋統計模型
# ==========================================

class IssueTagCount(BaseModel):
    """問題標籤計數"""
    tag: str = Field(..., description="標籤名稱")
    count: int = Field(..., description="出現次數")


class FeedbackStats(BaseModel):
    """AI 品質反饋統計"""
    total_feedbacks: int = Field(..., description="總反饋數")
    thumbs_up_count: int = Field(..., description="讚數")
    thumbs_down_count: int = Field(..., description="踩數")
    thumbs_up_rate: float = Field(..., description="讚比例 (%)")
    feedback_rate: float = Field(..., description="反饋率 (%)")
    pending_review_count: int = Field(..., description="待審查反饋數")
    top_issue_tags: List[IssueTagCount] = Field(..., description="常見問題標籤 Top 10")

    class Config:
        json_schema_extra = {
            "example": {
                "total_feedbacks": 234,
                "thumbs_up_count": 189,
                "thumbs_down_count": 45,
                "thumbs_up_rate": 80.77,
                "feedback_rate": 18.96,
                "pending_review_count": 12,
                "top_issue_tags": [
                    {"tag": "回答不準確", "count": 23},
                    {"tag": "內容太簡短", "count": 15}
                ]
            }
        }


# ==========================================
# Admin 儀表板回應
# ==========================================

class AdminDashboardStats(BaseModel):
    """Admin 儀表板統計數據"""
    time_range: str = Field(..., description="時間範圍")
    period_start: Optional[datetime] = Field(None, description="統計期間起始時間")
    period_end: datetime = Field(..., description="統計期間結束時間")
    chat_stats: ChatStats = Field(..., description="聊天互動統計")
    feedback_stats: FeedbackStats = Field(..., description="AI 品質反饋統計")

    class Config:
        json_schema_extra = {
            "example": {
                "time_range": "last_7_days",
                "period_start": "2025-11-19T00:00:00Z",
                "period_end": "2025-11-26T23:59:59Z",
                "chat_stats": {
                    "total_sessions": 156,
                    "total_messages": 1234,
                    "daily_avg_messages": 45.2,
                    "graph_type_distribution": {
                        "base_graph": 45,
                        "rag_graph": 89,
                        "deep_research": 22
                    }
                },
                "feedback_stats": {
                    "total_feedbacks": 234,
                    "thumbs_up_count": 189,
                    "thumbs_down_count": 45,
                    "thumbs_up_rate": 80.77,
                    "feedback_rate": 18.96,
                    "pending_review_count": 12,
                    "top_issue_tags": [
                        {"tag": "回答不準確", "count": 23},
                        {"tag": "內容太簡短", "count": 15}
                    ]
                }
            }
        }


# ==========================================
# User 儀表板回應
# ==========================================

class BasicStats(BaseModel):
    """基本統計"""
    total_sessions: int = Field(..., description="總對話數")
    total_messages: int = Field(..., description="總訊息數")


class UserDashboardInfo(BaseModel):
    """User 儀表板資訊"""
    username: str = Field(..., description="使用者名稱")
    welcome_message: str = Field(..., description="歡迎訊息")
    basic_stats: BasicStats = Field(..., description="基本統計")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "welcome_message": "歡迎回來, john_doe! 👋",
                "basic_stats": {
                    "total_sessions": 12,
                    "total_messages": 89
                }
            }
        }
