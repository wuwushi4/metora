# -*- coding: utf-8 -*-
"""
LLM Provider 抽象基類
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any


class BaseLLMProvider(ABC):
    """LLM 提供商基礎抽象類別"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM Provider

        Args:
            config: 配置參數字典
        """
        self.config = config

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        生成完整回應

        Args:
            prompt: 輸入提示
            temperature: 溫度參數（控制隨機性）
            max_tokens: 最大 token 數
            **kwargs: 其他參數

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        串流生成回應

        Args:
            prompt: 輸入提示
            temperature: 溫度參數
            max_tokens: 最大 token 數
            **kwargs: 其他參數

        Yields:
            生成的文本片段
        """
        pass

    @abstractmethod
    def to_langchain_llm(self):
        """
        轉換為 LangChain 的 LLM 物件

        Returns:
            LangChain 的 LLM 實例
        """
        pass
