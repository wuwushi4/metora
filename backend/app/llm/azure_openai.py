# -*- coding: utf-8 -*-
"""
Azure OpenAI LLM Provider 實作
使用 Azure OpenAI Service API
"""
import json
from typing import AsyncGenerator, Optional, Dict, Any

import aiohttp
from langchain_openai import AzureChatOpenAI

from app.llm.base import BaseLLMProvider


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI LLM 提供商"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Azure OpenAI Provider

        Args:
            config: 配置參數，應包含:
                - api_key: Azure OpenAI API Key（必填）
                - endpoint: Azure OpenAI 端點 URL（必填）
                - deployment_name: 部署名稱（必填）
                - api_version: API 版本
                - temperature: 溫度參數
                - max_tokens: 最大 token 數
                - timeout: 請求超時時間
                - top_p: Top-p 採樣參數

        Raises:
            ValueError: 如果必填參數為空
        """
        super().__init__(config)

        self.api_key = config.get("api_key", "")
        self.endpoint = config.get("endpoint", "").rstrip("/")
        self.deployment_name = config.get("deployment_name", "")

        if not self.api_key:
            raise ValueError(
                "Azure OpenAI API Key 不可為空，請設定 AZURE_OPENAI_API_KEY 環境變數"
            )
        if not self.endpoint:
            raise ValueError(
                "Azure OpenAI Endpoint 不可為空，請設定 AZURE_OPENAI_ENDPOINT 環境變數"
            )
        if not self.deployment_name:
            raise ValueError(
                "Azure OpenAI Deployment Name 不可為空，"
                "請設定 AZURE_OPENAI_DEPLOYMENT_NAME 環境變數"
            )

        self.api_version = config.get("api_version", "2024-08-01-preview")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60.0)
        self.default_top_p = config.get("top_p", 1.0)

    def _build_url(self) -> str:
        """建立 Azure OpenAI API URL"""
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment_name}"
            f"/chat/completions?api-version={self.api_version}"
        )

    def _build_headers(self) -> Dict[str, str]:
        """建立 API 請求標頭（Azure 使用 api-key 標頭）"""
        return {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        使用 Azure OpenAI API 生成完整回應

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
                self._build_url(),
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
        使用 Azure OpenAI API 串流生成回應

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
                self._build_url(),
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
        轉換為 LangChain 的 AzureChatOpenAI 物件

        Returns:
            AzureChatOpenAI 實例
        """
        return AzureChatOpenAI(
            azure_endpoint=self.endpoint,
            azure_deployment=self.deployment_name,
            api_version=self.api_version,
            api_key=self.api_key,
            temperature=self.default_temperature,
            max_tokens=self.default_max_tokens,
            top_p=self.default_top_p,
        )
