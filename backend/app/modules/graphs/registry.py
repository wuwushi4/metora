# -*- coding: utf-8 -*-
"""
Graph 註冊中心：管理所有可用的 Graph
"""
from typing import Dict, List, Any
from langgraph.graph.state import CompiledStateGraph


class GraphRegistry:
    """Graph 註冊中心：管理所有可用的 Graph"""

    _graphs: Dict[str, CompiledStateGraph] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        graph: CompiledStateGraph,
        description: str = "",
        supports_collections: bool = False
    ):
        """
        註冊 Graph

        Args:
            name: Graph 名稱 (base_graph | rag_graph | deep_research)
            graph: 編譯後的 Graph
            description: 描述
            supports_collections: 是否支援 Collections 選擇
        """
        cls._graphs[name] = graph
        cls._metadata[name] = {
            "name": name,
            "description": description,
            "supports_collections": supports_collections
        }

    @classmethod
    def get(cls, name: str) -> CompiledStateGraph:
        """
        取得 Graph

        Args:
            name: Graph 名稱

        Returns:
            編譯後的 Graph

        Raises:
            ValueError: 如果 Graph 不存在
        """
        if name not in cls._graphs:
            raise ValueError(f"Graph '{name}' 未註冊")
        return cls._graphs[name]

    @classmethod
    def list_available(cls) -> List[Dict[str, Any]]:
        """
        列出所有可用的 Graph

        Returns:
            Graph metadata 列表
        """
        return list(cls._metadata.values())

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        檢查 Graph 是否存在

        Args:
            name: Graph 名稱

        Returns:
            是否存在
        """
        return name in cls._graphs

    @classmethod
    def unregister(cls, name: str):
        """
        取消註冊 Graph

        Args:
            name: Graph 名稱
        """
        if name in cls._graphs:
            del cls._graphs[name]
            del cls._metadata[name]

    @classmethod
    def clear(cls):
        """清空所有註冊的 Graph"""
        cls._graphs.clear()
        cls._metadata.clear()


def initialize_graphs(settings, llm_provider, retrieval_service):
    """
    初始化並註冊所有 Graph

    Args:
        settings: 應用設定物件
        llm_provider: LLM Provider 實例
        retrieval_service: RetrievalService 實例
    """
    from app.modules.graphs.definitions.base_graph import create_base_graph
    from app.modules.graphs.definitions.rag_graph import create_rag_graph
    from app.modules.graphs.definitions.regulation_graph import create_regulation_graph

    # 註冊 base_graph
    base_graph = create_base_graph(settings, llm_provider)
    GraphRegistry.register(
        name="base_graph",
        graph=base_graph,
        description="基礎對話 Graph，不進行 RAG 檢索",
        supports_collections=False
    )

    # 註冊 rag_graph
    rag_graph = create_rag_graph(settings, llm_provider, retrieval_service)
    GraphRegistry.register(
        name="rag_graph",
        graph=rag_graph,
        description="RAG 對話 Graph，支援知識庫檢索",
        supports_collections=True
    )

    # 註冊 regulation_graph
    regulation_graph = create_regulation_graph(settings, llm_provider, retrieval_service)
    GraphRegistry.register(
        name="regulation_graph",
        graph=regulation_graph,
        description="法規查詢和分析 Graph，支援引用關係追蹤和情境判斷",
        supports_collections=True
    )

    # 註冊 agent_graph（需要 Sandbox 功能啟用）
    if settings.SANDBOX_ENABLED:
        from app.modules.graphs.definitions.agent_graph import create_agent_graph
        from app.modules.sandbox.service import SandboxService

        sandbox_service = SandboxService(settings)
        agent_graph = create_agent_graph(settings, llm_provider, sandbox_service)
        GraphRegistry.register(
            name="agent_graph",
            graph=agent_graph,
            description="通用 AI Agent，支援程式碼執行等工具",
            supports_collections=False
        )
