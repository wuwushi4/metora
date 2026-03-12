# -*- coding: utf-8 -*-
"""
vLLM LLM Provider 實作
使用 OpenAI-compatible API
"""
import json
from typing import AsyncGenerator, Optional, Dict, Any

import aiohttp
from langchain_openai import ChatOpenAI

from app.llm.base import BaseLLMProvider


class VLLMProvider(BaseLLMProvider):
    """vLLM LLM 提供商"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 vLLM Provider

        Args:
            config: 配置參數，應包含:
                - base_url: vLLM API 基礎 URL
                - model: 模型名稱或路徑
                - temperature: 溫度參數
                - max_tokens: 最大 token 數
                - timeout: 請求超時時間
                - top_p: Top-p 採樣參數（核採樣）
                - top_k: Top-k 採樣參數
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8001")
        self.model = config.get("model", "Qwen3-VL-8B-Instruct-AWQ-4bit")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60.0)
        self.default_top_p = config.get("top_p", 0.95)
        self.default_top_k = config.get("top_k", 20)

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        使用 vLLM API 生成完整回應

        Args:
            prompt: 輸入提示
            temperature: 溫度參數
            max_tokens: 最大 token 數
            **kwargs: 其他參數 (frequency_penalty, presence_penalty 等)

        Returns:
            生成的文本
        """
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        # 組裝 OpenAI-compatible 請求格式
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": tokens,
            "stream": False,
            "top_p": self.default_top_p,
            "top_k": self.default_top_k,
        }

        # 合併額外參數
        payload.update(kwargs)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                result = await response.json()

                # 解析 OpenAI 格式回應
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
        使用 vLLM API 串流生成回應

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

        # 組裝 OpenAI-compatible 請求格式（串流模式）
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": tokens,
            "stream": True,
            "top_p": self.default_top_p,
            "top_k": self.default_top_k,
        }

        # 合併額外參數
        payload.update(kwargs)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()

                # 逐行讀取 SSE 串流回應
                async for line in response.content:
                    if line:
                        line_text = line.decode("utf-8").strip()

                        # 跳過空行
                        if not line_text:
                            continue

                        # 移除 SSE 格式前綴 "data: "
                        if line_text.startswith("data: "):
                            line_text = line_text[6:]

                        # 檢查結束標記
                        if line_text == "[DONE]":
                            break

                        try:
                            data = json.loads(line_text)
                            # 解析 OpenAI 格式串流回應
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if chunk := delta.get("content"):
                                    yield chunk
                        except json.JSONDecodeError:
                            # 跳過無法解析的行
                            continue

    def to_langchain_llm(self):
        """
        轉換為 LangChain 的 ChatOpenAI 物件
        使用 OpenAI-compatible API

        Returns:
            ChatOpenAI 實例
        """
        return ChatOpenAI(
            base_url=f"{self.base_url}/v1",
            model=self.model,
            temperature=self.default_temperature,
            max_tokens=self.default_max_tokens,
            top_p=self.default_top_p,  # top_p 是 OpenAI API 標準參數，顯式傳遞
            api_key="EMPTY",  # vLLM 不需要 API key，但 ChatOpenAI 要求此參數
            extra_body={
                "top_k": self.default_top_k,  # vLLM 專屬參數通過 extra_body 傳遞
            }
        )
