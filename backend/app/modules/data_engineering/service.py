# -*- coding: utf-8 -*-
"""
資料工程服務層

處理法規資料處理的業務邏輯
"""
import asyncio
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import requests

from app.modules.data_engineering.utils.scraper import LawScraper
from app.modules.data_engineering.utils.converter import MarkdownToRegulationConverter
from app.modules.data_engineering.schemas import LawStatistics
from app.modules.data_engineering.exceptions import ScrapingError, ConversionError
from app.utils.exceptions import AppException


class DataEngineeringService:
    """資料工程服務類別"""

    def __init__(self, db: AsyncSession, redis=None):
        """
        初始化服務

        Args:
            db: 資料庫 session
            redis: Redis 連線（可選）
        """
        self.db = db
        self.redis = redis
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_law(
        self,
        pcode: str,
        law_name: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        處理法規資料（爬蟲 + 轉換）

        Args:
            pcode: 法規編號
            law_name: 法規名稱（可選）
            force_refresh: 強制重新爬取

        Returns:
            包含 md_content, json_content, filenames, statistics 的字典

        Raises:
            ScrapingError: 爬取失敗
            ConversionError: 轉換失敗
            AppException: 其他錯誤
        """
        start_time = time.time()
        logger.info(f"開始處理法規：{pcode}，force_refresh={force_refresh}")

        # 檢查 Redis 快取
        from_cache = False
        if self.redis and not force_refresh:
            cached_result = await self._get_from_cache(pcode)
            if cached_result:
                logger.info(f"Redis 快取命中：{pcode}")
                cached_result['from_cache'] = True
                cached_result['processing_time'] = time.time() - start_time
                return cached_result

        # 步驟 1: 爬取法規 (HTML → Markdown)
        try:
            logger.debug(f"執行爬蟲：{pcode}")
            scraper = LawScraper(pcode)
            md_content, metadata = await self._run_scraper(scraper)

            # 如果未提供法規名稱，從元數據中提取
            if not law_name:
                law_name = metadata.get('name', '未知法規')
                logger.info(f"從網頁提取法規名稱：{law_name}")

            logger.success(f"爬蟲完成，Markdown 長度：{len(md_content)}")

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logger.warning(f"法規不存在：{pcode}")
                raise ScrapingError(pcode, "法規不存在（404）")
            logger.error(f"HTTP 錯誤：{e}")
            raise ScrapingError(pcode, f"網路錯誤：{str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"網路請求失敗：{e}")
            raise ScrapingError(pcode, f"網路連線失敗：{str(e)}")
        except Exception as e:
            logger.error(f"爬蟲失敗：{e}", exc_info=True)
            raise ScrapingError(pcode, f"解析錯誤：{str(e)}")

        # 步驟 2: 轉換 Markdown → JSON
        try:
            logger.debug(f"執行轉換：Markdown → JSON")
            converter = MarkdownToRegulationConverter(
                law_name=law_name,
                law_code=pcode,
                last_updated=metadata.get('date', '未知')
            )
            json_content = converter.convert(md_content)
            logger.success(f"轉換完成")

        except Exception as e:
            logger.error(f"轉換失敗：{e}", exc_info=True)
            raise ConversionError(
                str(e),
                {"pcode": pcode, "law_name": law_name}
            )

        # 步驟 3: 計算統計資訊
        statistics = self._calculate_statistics(json_content)
        logger.info(f"統計：{statistics.model_dump()}")

        # 步驟 4: 生成檔名
        safe_name = self._sanitize_filename(law_name)
        md_filename = f"{safe_name}_{pcode}.md"
        json_filename = f"{safe_name}_{pcode}.json"

        # 組裝結果
        result = {
            "pcode": pcode,
            "law_name": law_name,
            "md_content": md_content,
            "json_content": json_content,
            "md_filename": md_filename,
            "json_filename": json_filename,
            "statistics": statistics,
            "from_cache": from_cache,
            "processing_time": time.time() - start_time
        }

        # 儲存到 Redis 快取（7 天）
        if self.redis:
            await self._save_to_cache(pcode, result)

        return result

    async def _run_scraper(self, scraper: LawScraper) -> Tuple[str, Dict[str, str]]:
        """
        在線程池中執行同步爬蟲

        Args:
            scraper: LawScraper 實例

        Returns:
            (md_content, metadata)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            scraper.scrape
        )

    async def _get_from_cache(self, pcode: str) -> Optional[Dict[str, Any]]:
        """從 Redis 獲取快取"""
        try:
            cache_key = f"law:processed:{pcode}"
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis 讀取失敗：{e}")
        return None

    async def _save_to_cache(self, pcode: str, result: Dict[str, Any]) -> None:
        """儲存到 Redis 快取"""
        try:
            cache_key = f"law:processed:{pcode}"
            # 移除不需要快取的欄位
            cache_data = result.copy()
            cache_data.pop('processing_time', None)

            # 將 Pydantic 模型轉換為字典
            if 'statistics' in cache_data and hasattr(cache_data['statistics'], 'model_dump'):
                cache_data['statistics'] = cache_data['statistics'].model_dump()

            await self.redis.setex(
                cache_key,
                7 * 24 * 3600,  # 7 天
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.debug(f"已儲存到 Redis 快取：{pcode}")
        except Exception as e:
            logger.warning(f"Redis 儲存失敗：{e}")

    def _calculate_statistics(self, json_content: Dict[str, Any]) -> LawStatistics:
        """計算統計資訊"""
        chapters = len(json_content.get('chapters', []))
        articles = sum(
            len(chapter.get('articles', []))
            for chapter in json_content.get('chapters', [])
        )
        items = sum(
            len(article.get('items', []))
            for chapter in json_content.get('chapters', [])
            for article in chapter.get('articles', [])
        )
        subitems = sum(
            len(item.get('subitems', []))
            for chapter in json_content.get('chapters', [])
            for article in chapter.get('articles', [])
            for item in article.get('items', [])
        )

        return LawStatistics(
            chapters=chapters,
            articles=articles,
            items=items,
            subitems=subitems
        )

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理檔名（移除非法字元）

        Args:
            filename: 原始檔名

        Returns:
            清理後的檔名
        """
        # 移除 Windows/Linux 非法字元
        safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除前後空白
        safe = safe.strip()
        # 限制長度
        return safe[:50] if len(safe) > 50 else safe
