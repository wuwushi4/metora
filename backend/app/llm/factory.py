# -*- coding: utf-8 -*-
"""
LLM Provider 工廠類別
"""
from typing import Dict, Any

from app.llm.base import BaseLLMProvider
from app.llm.ollama import OllamaProvider
from app.llm.vllm import VLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.azure_openai import AzureOpenAIProvider
from app.llm.google_gemini import GoogleGeminiProvider


class LLMProviderFactory:
    """LLM 提供商工廠"""

    _providers = {
        "ollama": OllamaProvider,
        "vllm": VLLMProvider,
        "openai": OpenAIProvider,
        "azure_openai": AzureOpenAIProvider,
        "google_gemini": GoogleGeminiProvider,
    }

    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> BaseLLMProvider:
        """
        建立 LLM 提供商實例

        Args:
            provider_type: 提供商類型 (ollama | vllm | openai | azure_openai | google_gemini)
            config: 配置參數字典

        Returns:
            LLM 提供商實例

        Raises:
            ValueError: 如果提供商類型不支援
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"不支援的 LLM 提供商: {provider_type}。"
                f"支援的類型: {', '.join(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_type]
        return provider_class(config)

    @classmethod
    def create_from_settings(cls, settings) -> BaseLLMProvider:
        """
        從 settings 建立預設 LLM 提供商

        Args:
            settings: 應用設定物件（來自 core.config）

        Returns:
            LLM 提供商實例
        """
        # 從 settings 讀取配置
        provider_type = settings.LLM_PROVIDER.lower()

        if provider_type == "ollama":
            config = {
                "base_url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_MODEL,
                "temperature": settings.OLLAMA_TEMPERATURE,
                "max_tokens": settings.OLLAMA_MAX_TOKENS,
                "timeout": settings.OLLAMA_TIMEOUT,
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
                "top_p": settings.OLLAMA_TOP_P,
                "top_k": settings.OLLAMA_TOP_K,
            }
        elif provider_type == "vllm":
            config = {
                "base_url": settings.VLLM_BASE_URL,
                "model": settings.VLLM_MODEL,
                "temperature": settings.VLLM_TEMPERATURE,
                "max_tokens": settings.VLLM_MAX_TOKENS,
                "timeout": settings.VLLM_TIMEOUT,
                "top_p": settings.VLLM_TOP_P,
                "top_k": settings.VLLM_TOP_K,
            }
        elif provider_type == "openai":
            config = {
                "api_key": settings.OPENAI_API_KEY,
                "model": settings.OPENAI_MODEL,
                "base_url": settings.OPENAI_BASE_URL,
                "temperature": settings.OPENAI_TEMPERATURE,
                "max_tokens": settings.OPENAI_MAX_TOKENS,
                "timeout": settings.OPENAI_TIMEOUT,
                "top_p": settings.OPENAI_TOP_P,
                "organization": settings.OPENAI_ORGANIZATION,
            }
        elif provider_type == "azure_openai":
            config = {
                "api_key": settings.AZURE_OPENAI_API_KEY,
                "endpoint": settings.AZURE_OPENAI_ENDPOINT,
                "deployment_name": settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                "api_version": settings.AZURE_OPENAI_API_VERSION,
                "temperature": settings.AZURE_OPENAI_TEMPERATURE,
                "max_tokens": settings.AZURE_OPENAI_MAX_TOKENS,
                "timeout": settings.AZURE_OPENAI_TIMEOUT,
                "top_p": settings.AZURE_OPENAI_TOP_P,
            }
        elif provider_type == "google_gemini":
            config = {
                "api_key": settings.GOOGLE_API_KEY,
                "model": settings.GOOGLE_GEMINI_MODEL,
                "temperature": settings.GOOGLE_GEMINI_TEMPERATURE,
                "max_tokens": settings.GOOGLE_GEMINI_MAX_TOKENS,
                "timeout": settings.GOOGLE_GEMINI_TIMEOUT,
                "top_p": settings.GOOGLE_GEMINI_TOP_P,
                "top_k": settings.GOOGLE_GEMINI_TOP_K,
            }
        else:
            config = {}

        return cls.create(provider_type, config)

    @classmethod
    def register(cls, name: str, provider_class: type):
        """
        註冊自訂 LLM Provider

        Args:
            name: Provider 名稱
            provider_class: Provider 類別（必須繼承 BaseLLMProvider）

        Raises:
            TypeError: 如果 provider_class 不是 BaseLLMProvider 的子類
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise TypeError(
                f"{provider_class.__name__} 必須繼承 BaseLLMProvider"
            )

        cls._providers[name] = provider_class

    @classmethod
    def list_available(cls) -> list[str]:
        """
        列出所有可用的 Provider 類型

        Returns:
            Provider 名稱列表
        """
        return list(cls._providers.keys())
