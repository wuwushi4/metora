# -*- coding: utf-8 -*-
"""
Regulation 管理相關的 Pydantic Schemas
定義 Regulation CRUD 的 API 請求和響應結構
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import inspect


# ===========================================
# 法規內容結構 Schemas
# ===========================================

class LawMetadata(BaseModel):
    """法規基本資料"""
    name: str = Field(..., description="法規名稱")
    category: str = Field(..., description="法規類別")
    status: str = Field(..., description="法規狀態（現行/廢止等）")
    last_updated: str = Field(..., description="最後更新日期（YYYY-MM-DD）")
    code: str = Field(..., description="法規代碼（如：D0050001）")
    source_url: str = Field(..., description="法規來源網址")

    @model_validator(mode='before')
    @classmethod
    def ensure_required_fields(cls, values):
        """確保 code 與 source_url 存在，並與舊資料相容"""
        if not isinstance(values, dict):
            return values

        code = values.get("code") or values.get("pcode")
        if not code:
            raise ValueError("law_metadata.code 為必填欄位")
        values["code"] = code
        values.pop("pcode", None)

        source_url = values.get("source_url")
        if not source_url and code:
            values["source_url"] = f"https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={code}"

        return values

    model_config = {"from_attributes": True}


class Article(BaseModel):
    """條文結構"""
    article_num: str = Field(..., description="條文編號（如：1、14-2）")
    article_display: str = Field(..., description="條文顯示名稱（如：第 1 條）")
    content: str = Field(..., description="條文內容")
    scenarios: List[str] = Field(default_factory=list, description="應用情境列表")

    model_config = {
        "from_attributes": True,
        "extra": "allow"  # 允許額外欄位（items, references, note, article_url 等），保留完整 JSON 結構
    }


class Chapter(BaseModel):
    """章節結構"""
    chapter_num: str = Field(..., description="章節編號（如：1、4-1）")
    chapter_display: str = Field(..., description="章節顯示名稱（如：第 一 章）")
    chapter_name: str = Field(..., description="章節名稱（如：總則）")
    articles: List[Article] = Field(default_factory=list, description="該章節下的條文列表")

    @field_validator('articles')
    @classmethod
    def validate_articles_count(cls, v: List[Article]) -> List[Article]:
        """驗證條文數量（防止 DoS）"""
        if len(v) > 500:
            raise ValueError(f"單一章節的條文數量不得超過 500 條，當前：{len(v)} 條")
        return v

    model_config = {"from_attributes": True}


class RegulationContent(BaseModel):
    """完整法規內容結構（用於驗證 JSONB）"""
    law_metadata: LawMetadata = Field(..., description="法規基本資料")
    chapters: List[Chapter] = Field(default_factory=list, description="章節列表")

    @field_validator('chapters')
    @classmethod
    def validate_chapters_count(cls, v: List[Chapter]) -> List[Chapter]:
        """驗證章節數量（防止 DoS）"""
        if len(v) > 1000:
            raise ValueError(f"法規章節數量不得超過 1000 章，當前：{len(v)} 章")
        return v

    model_config = {"from_attributes": True}


# ===========================================
# Regulation CRUD Schemas
# ===========================================

class OwnerInfo(BaseModel):
    """所有者資訊"""
    id: int = Field(..., description="使用者ID")
    username: str = Field(..., description="使用者名稱")
    full_name: Optional[str] = Field(None, description="真實姓名")

    model_config = {"from_attributes": True}


class RegulationUploadRequest(BaseModel):
    """上傳法規請求"""
    content: RegulationContent = Field(..., description="完整法規內容（JSON格式）")

    @model_validator(mode='after')
    def validate_content_size(self):
        """驗證內容大小"""
        # 驗證章節數量
        chapters = self.content.chapters
        if len(chapters) > 1000:
            raise ValueError(f"法規章節數量不得超過 1000 章，當前：{len(chapters)} 章")

        # 驗證總條文數量
        total_articles = sum(len(chapter.articles) for chapter in chapters)
        if total_articles > 10000:
            raise ValueError(f"法規總條文數量不得超過 10000 條，當前：{total_articles} 條")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": {
                        "law_metadata": {
                            "name": "動物保護法",
                            "category": "農業類",
                            "status": "現行",
                            "last_updated": "2021-05-19",
                            "code": "M0060027",
                            "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0060027"
                        },
                        "chapters": [
                            {
                                "chapter_num": "1",
                                "chapter_display": "第 一 章",
                                "chapter_name": "總則",
                                "articles": [
                                    {
                                        "article_num": "1",
                                        "article_display": "第 1 條",
                                        "content": "為尊重動物生命及保護動物，特制定本法。",
                                        "scenarios": []
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }


class RegulationUpdateRequest(BaseModel):
    """更新法規請求（僅更新 scenarios）"""
    content: RegulationContent = Field(..., description="完整法規內容（包含更新後的 scenarios）")

    @model_validator(mode='after')
    def validate_content_size(self):
        """驗證內容大小"""
        chapters = self.content.chapters
        if len(chapters) > 1000:
            raise ValueError(f"法規章節數量不得超過 1000 章，當前：{len(chapters)} 章")

        total_articles = sum(len(chapter.articles) for chapter in chapters)
        if total_articles > 10000:
            raise ValueError(f"法規總條文數量不得超過 10000 條，當前：{total_articles} 條")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": {
                        "law_metadata": {
                            "name": "動物保護法",
                            "category": "農業類",
                            "status": "現行",
                            "last_updated": "2021-05-19",
                            "code": "M0060027",
                            "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0060027"
                        },
                        "chapters": [
                            {
                                "chapter_num": "1",
                                "chapter_display": "第 一 章",
                                "chapter_name": "總則",
                                "articles": [
                                    {
                                        "article_num": "1",
                                        "article_display": "第 1 條",
                                        "content": "為尊重動物生命及保護動物，特制定本法。",
                                        "scenarios": ["寵物飼養", "動物福利"]
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }


class RegulationResponse(BaseModel):
    """法規響應（包含計算的統計資料）"""
    id: int = Field(..., description="法規ID")
    law_code: str = Field(..., description="法規代碼")
    law_name: str = Field(..., description="法規名稱")
    category: str = Field(..., description="法規類別")
    status: str = Field(..., description="法規狀態")
    last_updated: Optional[str] = Field(None, description="最後更新日期")
    user_id: int = Field(..., description="所有者ID")

    # 計算的統計資料
    total_chapters: int = Field(default=0, description="章節總數")
    total_articles: int = Field(default=0, description="條文總數")
    total_scenarios: int = Field(default=0, description="情境總數")

    owner: Optional[OwnerInfo] = Field(None, description="所有者資訊")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "law_code": "M0060027",
                    "law_name": "動物保護法",
                    "category": "農業類",
                    "status": "現行",
                    "last_updated": "2021-05-19",
                    "user_id": 1,
                    "total_chapters": 8,
                    "total_articles": 35,
                    "total_scenarios": 120,
                    "owner": {
                        "id": 1,
                        "username": "admin",
                        "full_name": "系統管理員"
                    },
                    "created_at": "2025-01-15T10:00:00Z",
                    "updated_at": "2025-01-15T10:00:00Z"
                }
            ]
        }
    }

    @classmethod
    def from_orm_with_stats(cls, regulation) -> "RegulationResponse":
        """
        從 ORM 模型創建響應，並計算統計資料

        Args:
            regulation: Regulation ORM 模型實例

        Returns:
            RegulationResponse: 包含統計資料的響應模型
        """
        # 檢查 content 是否已加載（避免觸發 lazy loading）
        if 'content' in regulation.__dict__:
            content = regulation.__dict__['content']
        else:
            # content 未加載，使用預設值
            content = {'chapters': []}

        # 計算章節總數
        total_chapters = len(content.get('chapters', []))

        # 計算條文總數
        total_articles = sum(
            len(chapter.get('articles', []))
            for chapter in content.get('chapters', [])
        )

        # 計算情境總數
        total_scenarios = sum(
            len(article.get('scenarios', []))
            for chapter in content.get('chapters', [])
            for article in chapter.get('articles', [])
        )

        # 提取 law_metadata
        law_metadata = content.get('law_metadata', {})

        # 創建 owner info
        owner = None
        # 檢查 user 是否已在實例的 __dict__ 中（已加載）
        # 這樣可以避免觸發 lazy loading
        if 'user' in regulation.__dict__:
            user = regulation.__dict__['user']
            if user:
                owner = OwnerInfo(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name
                )

        return cls(
            id=regulation.id,
            law_code=regulation.law_code,
            law_name=regulation.law_name,
            category=regulation.category,
            status=regulation.status,
            last_updated=regulation.last_updated,
            user_id=regulation.user_id,
            total_chapters=total_chapters,
            total_articles=total_articles,
            total_scenarios=total_scenarios,
            owner=owner,
            created_at=regulation.created_at,
            updated_at=regulation.updated_at
        )


class RegulationDetailResponse(BaseModel):
    """法規詳細響應（包含完整內容和統計資料）"""
    id: int = Field(..., description="法規ID")
    law_code: str = Field(..., description="法規代碼")
    law_name: str = Field(..., description="法規名稱")
    category: str = Field(..., description="法規類別")
    status: str = Field(..., description="法規狀態")
    last_updated: Optional[str] = Field(None, description="最後更新日期")
    user_id: int = Field(..., description="所有者ID")
    content: RegulationContent = Field(..., description="完整法規內容")

    # 統計資料
    total_chapters: int = Field(default=0, description="章節總數")
    total_articles: int = Field(default=0, description="條文總數")
    total_scenarios: int = Field(default=0, description="情境總數")

    owner: Optional[OwnerInfo] = Field(None, description="所有者資訊")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "law_code": "M0060027",
                    "law_name": "動物保護法",
                    "category": "農業類",
                    "status": "現行",
                    "last_updated": "2021-05-19",
                    "user_id": 1,
                    "content": {
                        "law_metadata": {
                            "name": "動物保護法",
                            "category": "農業類",
                            "status": "現行",
                            "last_updated": "2021-05-19",
                            "code": "M0060027",
                            "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0060027"
                        },
                        "chapters": []
                    },
                    "total_chapters": 8,
                    "total_articles": 35,
                    "total_scenarios": 120,
                    "owner": {
                        "id": 1,
                        "username": "admin",
                        "full_name": "系統管理員"
                    },
                    "created_at": "2025-01-15T10:00:00Z",
                    "updated_at": "2025-01-15T10:00:00Z"
                }
            ]
        }
    }

    @classmethod
    def from_orm_with_stats(cls, regulation) -> "RegulationDetailResponse":
        """
        從 ORM 模型創建響應，並計算統計資料

        Args:
            regulation: Regulation ORM 模型實例

        Returns:
            RegulationDetailResponse: 包含統計資料的響應模型
        """
        # 安全獲取 content（避免觸發 lazy loading）
        content = regulation.__dict__.get('content', {'chapters': []})

        # 計算統計資料
        total_chapters = len(content.get('chapters', []))
        total_articles = sum(
            len(chapter.get('articles', []))
            for chapter in content.get('chapters', [])
        )
        total_scenarios = sum(
            len(article.get('scenarios', []))
            for chapter in content.get('chapters', [])
            for article in chapter.get('articles', [])
        )

        # 創建 owner info
        owner = None
        if 'user' in regulation.__dict__:
            user = regulation.__dict__['user']
            if user:
                owner = OwnerInfo(
                    id=user.id,
                    username=user.username,
                    full_name=user.full_name
                )

        # 轉換 content 為 Pydantic 模型
        content_model = RegulationContent(**content)

        return cls(
            id=regulation.id,
            law_code=regulation.law_code,
            law_name=regulation.law_name,
            category=regulation.category,
            status=regulation.status,
            last_updated=regulation.last_updated,
            user_id=regulation.user_id,
            content=content_model,
            total_chapters=total_chapters,
            total_articles=total_articles,
            total_scenarios=total_scenarios,
            owner=owner,
            created_at=regulation.created_at,
            updated_at=regulation.updated_at
        )


class RegulationListParams(BaseModel):
    """法規列表查詢參數"""
    page: int = Field(default=1, ge=1, description="頁碼（從 1 開始）")
    page_size: int = Field(default=20, ge=1, le=100, description="每頁筆數（1-100）")
    law_name: Optional[str] = Field(None, description="法規名稱（模糊搜尋）")
    category: Optional[str] = Field(None, description="法規類別（精確搜尋）")
    status: Optional[str] = Field(None, description="法規狀態（精確搜尋）")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 1,
                    "page_size": 20,
                    "law_name": "動物保護",
                    "category": "農業類",
                    "status": "現行"
                }
            ]
        }
    }
