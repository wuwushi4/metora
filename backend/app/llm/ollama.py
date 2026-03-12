# -*- coding: utf-8 -*-
"""
Ollama LLM Provider 實作
"""
import json
from typing import AsyncGenerator, Optional, Dict, Any

import aiohttp
from langchain_ollama import ChatOllama

from app.llm.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM 提供商"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Ollama Provider

        Args:
            config: 配置參數，應包含:
                - base_url: Ollama API 基礎 URL
                - model: 模型名稱
                - temperature: 溫度參數
                - max_tokens: 最大 token 數
                - timeout: 請求超時時間
                - keep_alive: 模型保持活躍時間
                - top_p: Top-p 採樣參數（核採樣）
                - top_k: Top-k 採樣參數
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "gemma3:12b")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 30.0)
        self.keep_alive = config.get("keep_alive", "5m")
        self.default_top_p = config.get("top_p", 0.6)
        self.default_top_k = config.get("top_k", 40)

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        使用 Ollama API 生成完整回應

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
            "prompt": prompt,
            "temperature": temp,
            "num_predict": tokens,
            "stream": False,
            "keep_alive": self.keep_alive,
            "top_p": self.default_top_p,
            "top_k": self.default_top_k,
        }

        # 合併額外參數
        payload.update(kwargs)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("response", "")

    async def stream_generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        使用 Ollama API 串流生成回應

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
            "prompt": prompt,
            "temperature": temp,
            "num_predict": tokens,
            "stream": True,
            "keep_alive": self.keep_alive,
            "top_p": self.default_top_p,
            "top_k": self.default_top_k,
        }

        # 合併額外參數
        payload.update(kwargs)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()

                # 逐行讀取串流回應
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if chunk := data.get("response"):
                                yield chunk
                        except json.JSONDecodeError:
                            # 跳過無法解析的行
                            continue

    def to_langchain_llm(self):
        """
        轉換為 LangChain 的 ChatOllama 物件

        Returns:
            ChatOllama 實例
        """
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=self.default_temperature,
            num_predict=self.default_max_tokens,
            keep_alive=self.keep_alive,
            top_p=self.default_top_p,
            top_k=self.default_top_k,
        )
