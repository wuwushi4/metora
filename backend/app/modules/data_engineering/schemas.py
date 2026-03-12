# -*- coding: utf-8 -*-
"""
資料工程模組相關的 Pydantic Schemas
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class LawProcessRequest(BaseModel):
    """處理法規請求"""

    pcode: str = Field(
        ...,
        description="法規編號（格式：1個英文字母 + 7位數字）",
        examples=["M0060027"]
    )
    law_name: Optional[str] = Field(
        None,
        description="法規名稱（可選，如未提供則從網頁提取）",
        max_length=200
    )
    force_refresh: bool = Field(
        False,
        description="強制重新爬取（忽略快取）"
    )

    @field_validator('pcode')
    @classmethod
    def validate_pcode(cls, v: str) -> str:
        """驗證法規編號格式"""
        v = v.strip().upper()
        if not re.match(r'^[A-Z]\d{7}$', v):
            raise ValueError(
                "法規編號格式錯誤，正確格式為：1個大寫英文字母 + 7個數字（例如：M0060027）"
            )
        return v

    @field_validator('law_name')
    @classmethod
    def validate_law_name(cls, v: Optional[str]) -> Optional[str]:
        """驗證法規名稱"""
        if v:
            v = v.strip()
            if not v:
                return None
        return v


class LawStatistics(BaseModel):
    """法規統計資訊"""

    chapters: int = Field(..., description="章數")
    articles: int = Field(..., description="條數")
    items: int = Field(..., description="項數")
    subitems: int = Field(..., description="款數")


class LawProcessResponse(BaseModel):
    """處理法規回應"""

    pcode: str = Field(..., description="法規編號")
    law_name: str = Field(..., description="法規名稱")
    md_content: str = Field(..., description="Markdown 內容")
    json_content: Dict[str, Any] = Field(..., description="JSON 內容")
    md_filename: str = Field(..., description="建議的 Markdown 檔名")
    json_filename: str = Field(..., description="建議的 JSON 檔名")
    statistics: LawStatistics = Field(..., description="統計資訊")
    from_cache: bool = Field(False, description="是否來自快取")
    processing_time: Optional[float] = Field(None, description="處理耗時（秒）")
