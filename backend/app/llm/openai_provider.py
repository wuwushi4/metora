# -*- coding: utf-8 -*-
"""
OpenAI LLM Provider 實作
使用 OpenAI Chat Completions API
"""
import json
from typing import AsyncGenerator, Optional, Dict, Any

import aiohttp
from langchain_openai import ChatOpenAI

from app.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM 提供商"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 OpenAI Provider

        Args:
            config: 配置參數，應包含:
                - api_key: OpenAI API Key（必填）
                - model: 模型名稱
                - base_url: API 基礎 URL
                - temperature: 溫度參數
                - max_tokens: 最大 token 數
                - timeout: 請求超時時間
                - top_p: Top-p 採樣參數
                - organization: OpenAI 組織 ID（可選）

        Raises:
            ValueError: 如果 api_key 為空
        """
        super().__init__(config)

        self.api_key = config.get("api_key", "")
        if not self.api_key:
            raise ValueError("OpenAI API Key 不可為空，請設定 OPENAI_API_KEY 環境變數")

        self.model = config.get("model", "gpt-4o")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60.0)
        self.default_top_p = config.get("top_p", 1.0)
        self.organization = config.get("organization", "")

    def _build_headers(self) -> Dict[str, str]:
        """建立 API 請求標頭"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        使用 OpenAI API 生成完整回應

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

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": tokens,
            "stream": False,
            "top_p": self.default_top_p,
        }
        payload.update(kwargs)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._build_headers(),
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return ""

    async def stream_generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        使用 OpenAI API 串流生成回應

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

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": tokens,
            "stream": True,
            "top_p": self.default_top_p,
        }
        payload.update(kwargs)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._build_headers(),
            ) as response:
                response.raise_for_status()

                async for line in response.content:
                    if line:
                        line_text = line.decode("utf-8").strip()

                        if not line_text:
                            continue

                        if line_text.startswith("data: "):
                            line_text = line_text[6:]

                        if line_text == "[DONE]":
                            break

                        try:
                            data = json.loads(line_text)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if chunk := delta.get("content"):
                                    yield chunk
                        except json.JSONDecodeError:
                            continue

    def to_langchain_llm(self):
        """
        轉換為 LangChain 的 ChatOpenAI 物件

        Returns:
            ChatOpenAI 實例
        """
        kwargs = {
            "model": self.model,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
            "top_p": self.default_top_p,
            "api_key": self.api_key,
            "base_url": self.base_url,
        }
        if self.organization:
            kwargs["organization"] = self.organization

        return ChatOpenAI(**kwargs)
