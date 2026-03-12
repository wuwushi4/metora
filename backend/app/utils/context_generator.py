# -*- coding: utf-8 -*-
"""
LLM 情境生成器

使用 LLM 為法規條文生成自然語言的情境描述，
用於提升檢索時的召回率（多重表徵）。
"""
import asyncio
from typing import List, Optional
from loguru import logger

from app.llm.base import BaseLLMProvider


class ContextGenerator:
    """
    情境生成器

    使用 LLM 為法規條文生成適用情境描述，
    幫助使用者用自然語言查詢時能匹配到相關條文。
    """

    # 情境生成 Prompt 模板
    CONTEXT_GENERATION_PROMPT = """你是一位法律專家。請分析以下法規條文，用口語化、生活化的方式描述「一般民眾在什麼情況下會需要查詢這條法規」。

法規名稱：{law_name}
條號：{article_display}
條文內容：
{article_content}

請用自然、口語化的表達描述：
1. 這條法規適用於哪些具體的生活情境或場景？
2. 一般民眾在遇到什麼問題時會需要查這條法規？
3. 相關的關鍵場景和狀況

要求：
- 使用日常用語，避免法律術語
- 以情境和場景為主，不要重複法條原文
- 簡潔明瞭，3-5 句話即可
- 直接輸出情境描述，不要加其他說明

情境描述："""

    def __init__(self, llm_provider: BaseLLMProvider, temperature: float = 0.3):
        """
        初始化情境生成器

        Args:
            llm_provider: LLM Provider 實例
            temperature: 生成溫度，較低的溫度產生更穩定的輸出
        """
        self.llm_provider = llm_provider
        self.temperature = temperature
        self.max_tokens = 300  # 情境描述通常不需要太長

    async def generate_context(
        self,
        law_name: str,
        article_display: str,
        article_content: str,
        retry_count: int = 2
    ) -> Optional[str]:
        """
        為單個條文生成情境描述

        Args:
            law_name: 法規名稱
            article_display: 條號顯示（如"第3條"）
            article_content: 條文內容（含項款）
            retry_count: 失敗時的重試次數

        Returns:
            str: 生成的情境描述，失敗時返回 None
        """
        # 構建 Prompt
        prompt = self.CONTEXT_GENERATION_PROMPT.format(
            law_name=law_name,
            article_display=article_display,
            article_content=article_content[:500]  # 限制長度避免 token 超限
        )

        # 嘗試生成
        for attempt in range(retry_count + 1):
            try:
                logger.debug(
                    f"[ContextGenerator] 生成情境描述：{law_name} {article_display} "
                    f"(嘗試 {attempt + 1}/{retry_count + 1})"
                )

                # 調用 LLM
                context = await self.llm_provider.generate(
                    prompt=prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )

                # 清理輸出
                context = self._clean_context(context)

                if context and len(context.strip()) > 10:
                    logger.debug(
                        f"[ContextGenerator] 成功生成情境描述：{law_name} {article_display}"
                    )
                    return context

                logger.warning(
                    f"[ContextGenerator] 生成的情境描述過短或為空：{law_name} {article_display}"
                )

            except Exception as e:
                logger.error(
                    f"[ContextGenerator] 生成失敗：{law_name} {article_display}, "
                    f"錯誤：{e}, 嘗試 {attempt + 1}/{retry_count + 1}"
                )

                if attempt < retry_count:
                    # 短暫延遲後重試
                    await asyncio.sleep(1)
                else:
                    logger.error(
                        f"[ContextGenerator] 達到最大重試次數，放棄生成：{law_name} {article_display}"
                    )
                    return None

        return None

    async def generate_contexts_batch(
        self,
        articles: List[dict],
        law_name: str,
        max_concurrent: int = 5
    ) -> List[Optional[str]]:
        """
        批量並行生成情境描述

        Args:
            articles: 條文列表，每個條文包含：
                - article_display: 條號顯示
                - content: 條文內容
            law_name: 法規名稱
            max_concurrent: 最大並行數

        Returns:
            List[Optional[str]]: 情境描述列表（與輸入順序對應）
        """
        logger.info(
            f"[ContextGenerator] 開始批量生成情境描述：{law_name}, "
            f"共 {len(articles)} 條，最大並行數 {max_concurrent}"
        )

        # 創建任務
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(article: dict, index: int):
            """帶信號量控制的生成任務"""
            async with semaphore:
                try:
                    context = await self.generate_context(
                        law_name=law_name,
                        article_display=article.get("article_display", ""),
                        article_content=article.get("content", "")
                    )
                    logger.debug(f"[ContextGenerator] 完成 {index + 1}/{len(articles)}")
                    return context
                except Exception as e:
                    logger.error(f"[ContextGenerator] 任務失敗 {index + 1}/{len(articles)}: {e}")
                    return None

        # 執行所有任務
        tasks = [
            generate_with_semaphore(article, i)
            for i, article in enumerate(articles)
        ]

        contexts = await asyncio.gather(*tasks, return_exceptions=False)

        # 統計結果
        success_count = sum(1 for ctx in contexts if ctx is not None)
        logger.info(
            f"[ContextGenerator] 批量生成完成：{law_name}, "
            f"成功 {success_count}/{len(articles)}"
        )

        return contexts

    def _clean_context(self, context: str) -> str:
        """
        清理生成的情境描述

        Args:
            context: 原始情境描述

        Returns:
            str: 清理後的情境描述
        """
        if not context:
            return ""

        # 移除多餘的空白和換行
        context = context.strip()

        # 移除可能的 Markdown 標記
        context = context.replace("```", "").replace("**", "")

        # 移除可能的前綴（LLM 有時會加上）
        prefixes = ["情境描述：", "情境：", "適用情境：", "描述："]
        for prefix in prefixes:
            if context.startswith(prefix):
                context = context[len(prefix):].strip()

        return context

    def get_statistics(self) -> dict:
        """
        獲取生成統計資訊（預留介面，未來可擴展）

        Returns:
            dict: 統計資訊
        """
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


async def generate_regulation_contexts(
    llm_provider: BaseLLMProvider,
    law_name: str,
    articles: List[dict],
    temperature: float = 0.3,
    max_concurrent: int = 5
) -> List[Optional[str]]:
    """
    便利函數：為法規條文批量生成情境描述

    Args:
        llm_provider: LLM Provider 實例
        law_name: 法規名稱
        articles: 條文列表
        temperature: 生成溫度
        max_concurrent: 最大並行數

    Returns:
        List[Optional[str]]: 情境描述列表

    Example:
        >>> from app.llm.factory import LLMProviderFactory
        >>> from app.core.config import settings
        >>> llm_provider = LLMProviderFactory.create_from_settings(settings)
        >>> articles = [
        ...     {"article_display": "第3條", "content": "本法用詞..."},
        ...     {"article_display": "第4條", "content": "主管機關..."}
        ... ]
        >>> contexts = await generate_regulation_contexts(
        ...     llm_provider, "長期照顧服務法", articles
        ... )
    """
    generator = ContextGenerator(llm_provider, temperature)
    return await generator.generate_contexts_batch(
        articles=articles,
        law_name=law_name,
        max_concurrent=max_concurrent
    )
