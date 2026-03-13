# -*- coding: utf-8 -*-
"""
資料工程 API 路由
提供法規資料處理的 RESTful API 端點
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.dependencies import get_db, get_redis
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import UserInfo
from app.modules.data_engineering.service import DataEngineeringService
from app.modules.data_engineering.schemas import (
    LawProcessRequest,
    LawProcessResponse,
)
from app.modules.data_engineering.exceptions import ScrapingError, ConversionError
from app.i18n import t
from app.utils.response import ApiResponse, success_response
from loguru import logger

router = APIRouter(prefix="/data-engineering", tags=["資料工程"])


@router.post(
    "/laws/process",
    response_model=ApiResponse[LawProcessResponse],
    status_code=status.HTTP_200_OK,
    summary="處理法規資料",
    description="根據法規編號爬取法規並轉換為 Markdown 和 JSON 格式",
)
async def process_law(
    request: LawProcessRequest,
    current_user: Annotated[UserInfo, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    redis_client: Annotated[Optional[redis.Redis], Depends(get_redis)] = None,
):
    """
    處理法規資料

    權限要求:
    - 需要登入

    請求體:
    - pcode: 法規編號（1個大寫英文字母 + 7個數字，例如：M0060027）
    - law_name: 法規名稱（可選，如未提供則從網頁提取）
    - force_refresh: 強制重新爬取（忽略快取）

    回應:
    - pcode: 法規編號
    - law_name: 法規名稱
    - md_content: Markdown 格式內容
    - json_content: JSON 格式內容
    - md_filename: 建議的 Markdown 檔名
    - json_filename: 建議的 JSON 檔名
    - statistics: 統計資訊（章數、條數、項數、款數）
    - from_cache: 是否來自快取
    - processing_time: 處理耗時（秒）

    錯誤碼:
    - SCRAPING_ERROR: 爬取法規失敗（網路錯誤、法規不存在等）
    - CONVERSION_ERROR: 轉換失敗（格式錯誤等）
    """
    logger.info(
        f"User {current_user.username} (ID: {current_user.id}) "
        f"requested law processing for pcode: {request.pcode}"
    )

    # 創建服務實例
    service = DataEngineeringService(db=db, redis=redis_client)

    # 處理法規
    result = await service.process_law(
        pcode=request.pcode,
        law_name=request.law_name,
        force_refresh=request.force_refresh,
    )

    # 構建回應
    response = LawProcessResponse(
        pcode=result["pcode"],
        law_name=result["law_name"],
        md_content=result["md_content"],
        json_content=result["json_content"],
        md_filename=result["md_filename"],
        json_filename=result["json_filename"],
        statistics=result["statistics"],
        from_cache=result["from_cache"],
        processing_time=result["processing_time"],
    )

    logger.success(
        f"Law processing completed for pcode: {request.pcode}, "
        f"from_cache: {result['from_cache']}, "
        f"processing_time: {result['processing_time']:.2f}s"
    )

    return success_response(
        data=response,
        message=t('dataEngineering.processSuccess') if not result["from_cache"] else t('dataEngineering.processSuccessCached')
    )
