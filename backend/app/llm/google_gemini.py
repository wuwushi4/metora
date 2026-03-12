# -*- coding: utf-8 -*-
"""
Google Gemini LLM Provider 實作
使用 Google Generative AI REST API
"""
import json
from typing import AsyncGenerator, Optional, Dict, Any

import aiohttp
from langchain_google_genai import ChatGoogleGenerativeAI

from app.llm.base import BaseLLMProvider


class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini LLM 提供商"""

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Google Gemini Provider

        Args:
            config: 配置參數，應包含:
                - api_key: Google API Key（必填）
                - model: 模型名稱
                - temperature: 溫度參數
                - max_tokens: 最大 token 數
                - timeout: 請求超時時間
                - top_p: Top-p 採樣參數
                - top_k: Top-k 採樣參數

        Raises:
            ValueError: 如果 api_key 為空
        """
        super().__init__(config)

        self.api_key = config.get("api_key", "")
        if not self.api_key:
            raise ValueError(
                "Google API Key 不可為空，請設定 GOOGLE_API_KEY 環境變數"
            )

        self.model = config.get("model", "gemini-2.5-flash")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60.0)
        self.default_top_p = config.get("top_p", 1.0)
        self.default_top_k = config.get("top_k", 40)

    def _build_generation_config(
        self,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """建立 Gemini generationConfig"""
        return {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": self.default_top_p,
            "topK": self.default_top_k,
        }

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        使用 Gemini API 生成完整回應

        Args:
            prompt: 輸入提示
            temperature: 溫度參數
            max_tokens: 最大 token 數
            **kwargs: 其他參數

        Returns:
            生成的文本
        """
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        url = (
            f"{self.API_BASE}/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": self._build_generation_config(temp, tokens),
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()
                result = await response.json()

                # 解析 Gemini 回應格式
                candidates = result.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""

    async def stream_generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        使用 Gemini API 串流生成回應

        Args:
            prompt: 輸入提示
            temperature: 溫度參數
            max_tokens: 最大 token 數
            **kwargs: 其他參數

        Yields:
            生成的文本片段
        """
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        url = (
            f"{self.API_BASE}/models/{self.model}:streamGenerateContent"
            f"?alt=sse&key={self.api_key}"
        )

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": self._build_generation_config(temp, tokens),
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()

                async for line in response.content:
                    if line:
                        line_text = line.decode("utf-8").strip()

                        if not line_text:
                            continue

                        if line_text.startswith("data: "):
                            line_text = line_text[6:]

                        try:
                            data = json.loads(line_text)
                            candidates = data.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                if parts:
                                    if chunk := parts[0].get("text"):
                                        yield chunk
                        except json.JSONDecodeError:
                            continue

    def to_langchain_llm(self):
        """
        轉換為 LangChain 的 ChatGoogleGenerativeAI 物件

        Returns:
            ChatGoogleGenerativeAI 實例
        """
        return ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=self.default_temperature,
            max_output_tokens=self.default_max_tokens,
            top_p=self.default_top_p,
            top_k=self.default_top_k,
        )
