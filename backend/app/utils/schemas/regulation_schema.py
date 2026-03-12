# -*- coding: utf-8 -*-
"""
法規資料格式 Schema

定義法規資料的標準 JSON 格式，用於：
1. 爬蟲輸出驗證
2. 分塊器輸入驗證
3. 資料導入驗證
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator


class RegulationItem(BaseModel):
    """法規項（條文下的項）"""
    item_num: str = Field(..., description="項號，如 '1', '2'")
    item_display: str = Field(..., description="項號顯示文字，如 '一', '二'")
    content: str = Field(..., description="項的內容")
    subitems: List[Dict[str, Any]] = Field(default_factory=list, description="款（項下的子項）")


class RegulationReference(BaseModel):
    """法規引用關係"""
    raw_text: List[str] = Field(default_factory=list, description="原始引用文字，如 ['前條', '第2條']")
    resolved: List[str] = Field(default_factory=list, description="解析後的絕對條號，如 ['2', '8']")
    forward_refs: List[str] = Field(default_factory=list, description="向前引用（本條引用的其他條文）")
    backward_refs: List[str] = Field(default_factory=list, description="向後引用（引用本條的其他條文）")


class RegulationArticle(BaseModel):
    """法規條文"""
    article_num: str = Field(..., description="條號（數字），如 '3', '2-1'")
    article_display: str = Field(..., description="條號顯示文字，如 '第3條', '第2條之1'")
    content: str = Field(default="", description="條文內容（當有多個項時可為空）")
    items: List[RegulationItem] = Field(default_factory=list, description="條文下的項列表")
    references: Optional[RegulationReference] = Field(None, description="引用關係")
    note: Optional[str] = Field(None, description="備註或說明")
    scenarios: List[str] = Field(
        default_factory=list,
        description="適用情境描述列表（人工定義，用於提升檢索召回率）"
    )
    article_url: Optional[str] = Field(None, description="法規官網連結，如 'https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=D0040027&flno=3'")

    @validator('article_num')
    def validate_article_num(cls, v):
        """驗證條號格式"""
        if not v:
            raise ValueError("條號不能為空")
        # 允許數字和 -1, -2 這樣的分支
        return v.strip()

    @validator('content')
    def validate_content(cls, v):
        """驗證內容（允許為空，當有項時）"""
        return v.strip() if v else ""

    @validator('items')
    def validate_content_or_items(cls, v, values):
        """驗證 content 和 items 至少有一個不為空"""
        content = values.get('content', '').strip()
        if not content and not v:
            raise ValueError("條文的 content 和 items 不能同時為空")
        return v


class RegulationChapter(BaseModel):
    """法規章節"""
    chapter_num: str = Field(..., description="章號（數字），如 '1', '2'")
    chapter_name: str = Field(..., description="章名稱，如 '總則', '罰則'")
    chapter_display: str = Field(..., description="章顯示文字，如 '第一章', '第二章'")
    articles: List[RegulationArticle] = Field(..., description="本章的條文列表")

    @validator('articles')
    def validate_articles(cls, v):
        """驗證至少有一個條文"""
        if not v:
            raise ValueError("章節至少要有一個條文")
        return v


class RegulationMetadata(BaseModel):
    """法規元數據"""
    name: str = Field(..., description="法規名稱，如 '長期照顧服務法'")
    code: str = Field(..., description="法規編號，如 'L0070040'")
    source_url: Optional[str] = Field(None, description="來源網址")
    last_updated: Optional[str] = Field(None, description="最後更新日期，格式: YYYY-MM-DD")
    category: Optional[str] = Field(None, description="法規類別，如 '衛生福利類'")
    status: str = Field(default="現行", description="法規狀態：現行、廢止等")
    enacted_date: Optional[str] = Field(None, description="制定日期，格式: YYYY-MM-DD")

    @validator('name', 'code')
    def validate_required_fields(cls, v):
        """驗證必填欄位"""
        if not v or not v.strip():
            raise ValueError("法規名稱和編號為必填欄位")
        return v.strip()


class RegulationDocument(BaseModel):
    """完整的法規文件"""
    law_metadata: RegulationMetadata = Field(..., description="法規元數據")
    chapters: List[RegulationChapter] = Field(..., description="章節列表")

    @validator('chapters')
    def validate_chapters(cls, v):
        """驗證至少有一個章節"""
        if not v:
            raise ValueError("法規至少要有一個章節")
        return v

    def get_article_by_num(self, article_num: str) -> Optional[RegulationArticle]:
        """根據條號查找條文"""
        for chapter in self.chapters:
            for article in chapter.articles:
                if article.article_num == article_num:
                    return article
        return None

    def get_chapter_by_num(self, chapter_num: str) -> Optional[RegulationChapter]:
        """根據章號查找章節"""
        for chapter in self.chapters:
            if chapter.chapter_num == chapter_num:
                return chapter
        return None

    def count_articles(self) -> int:
        """統計總條文數"""
        return sum(len(chapter.articles) for chapter in self.chapters)

    def count_chapters(self) -> int:
        """統計總章數"""
        return len(self.chapters)

    class Config:
        json_schema_extra = {
            "example": {
                "law_metadata": {
                    "name": "長期照顧服務法",
                    "code": "L0070040",
                    "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0070040",
                    "last_updated": "2024-01-01",
                    "category": "衛生福利類",
                    "status": "現行",
                    "enacted_date": "2015-06-03"
                },
                "chapters": [
                    {
                        "chapter_num": "1",
                        "chapter_name": "總則",
                        "chapter_display": "第一章",
                        "articles": [
                            {
                                "article_num": "1",
                                "article_display": "第1條",
                                "content": "為健全長期照顧服務體系，確保照顧服務品質，維護接受服務者與照顧服務員之尊嚴及權益，特制定本法。",
                                "items": [],
                                "references": None,
                                "note": None,
                                "scenarios": [],
                                "article_url": "https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0070040&flno=1"
                            },
                            {
                                "article_num": "3",
                                "article_display": "第3條",
                                "content": "本法用詞，定義如下：",
                                "items": [
                                    {
                                        "item_num": "1",
                                        "item_display": "一",
                                        "content": "長期照顧：指身心失能持續已達或預期達六個月以上者，依其個人或其照顧者之需要，所提供之生活支持、協助、社會參與、照顧及相關之醫護服務。",
                                        "subitems": []
                                    },
                                    {
                                        "item_num": "2",
                                        "item_display": "二",
                                        "content": "長期照顧服務：指提供身心失能者生活支持、協助、社會參與、照顧及相關之醫護服務。",
                                        "subitems": []
                                    }
                                ],
                                "references": {
                                    "raw_text": [],
                                    "resolved": [],
                                    "forward_refs": [],
                                    "backward_refs": ["8"]
                                },
                                "note": None,
                                "scenarios": [
                                    "想了解什麼是長期照顧服務，有哪些內容",
                                    "家人需要長期照護，想知道法律上的定義"
                                ],
                                "article_url": "https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0070040&flno=3"
                            }
                        ]
                    }
                ]
            }
        }


def validate_regulation_json(json_data: Dict[str, Any]) -> RegulationDocument:
    """
    驗證法規 JSON 是否符合 Schema

    Args:
        json_data: 待驗證的 JSON 資料

    Returns:
        RegulationDocument: 驗證通過的法規文件對象

    Raises:
        ValidationError: 驗證失敗時拋出異常
    """
    return RegulationDocument(**json_data)


def regulation_to_dict(regulation: RegulationDocument) -> Dict[str, Any]:
    """
    將 RegulationDocument 轉換為字典

    Args:
        regulation: 法規文件對象

    Returns:
        Dict: 法規字典
    """
    return regulation.model_dump()
