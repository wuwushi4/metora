# -*- coding: utf-8 -*-
"""
基礎的 Graph：最簡單的對話流程，不包含 RAG 檢索
流程：START -> llm_node -> END
"""
from typing import TypedDict, List, Dict, Any
try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python < 3.11

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.modules.graphs.utils import (
    prepare_multimodal_message,
    ensure_system_message_first,
    extract_text_content,
)


class BaseGraphState(TypedDict):
    """基礎 Graph 狀態"""
    messages: List[BaseMessage]  # 對話歷史（最近 5 輪）
    user_query: str             # 當前使用者問題
    final_response: str         # 最終回應
    attachments: NotRequired[List[Dict[str, Any]]]  # 附件列表（Base64 格式）- 非必需欄位
    custom_system_prompt: NotRequired[str]  # 自訂系統提示詞 - 非必需欄位


def create_base_graph(settings, llm_provider) -> CompiledStateGraph:
    """
    建立基礎 Graph（簡單對話，無 RAG 檢索）

    Args:
        settings: 應用設定物件（來自 core.config）
        llm_provider: LLM Provider 實例

    Returns:
        CompiledStateGraph: 編譯後的 Graph

    注意：
        - 符合 LangGraph 1.0 最佳實踐
        - 使用輔助函數處理多模態輸入
        - 支援文字 + 圖片組合
        - 流程簡單：START -> llm -> END
    """
    # 取得 LangChain LLM 實例
    llm = llm_provider.to_langchain_llm()

    async def llm_node(state: BaseGraphState) -> BaseGraphState:
        """
        LLM 節點：使用最近 5 輪對話生成回應（異步，支援多模態，支援自訂提示詞）

        支援文字 + 圖片組合輸入，使用輔助函數處理多模態內容。
        """
        try:
            # 準備訊息列表（最近 5 輪 = 10 條訊息）
            messages = state["messages"].copy()

            # 如果有自訂系統提示詞，添加到訊息列表開頭
            if state.get("custom_system_prompt"):
                from langchain_core.messages import SystemMessage
                system_message = SystemMessage(content=state["custom_system_prompt"])
                messages.insert(0, system_message)

            # 使用輔助函數準備使用者訊息（支援多模態）
            user_message = prepare_multimodal_message(
                user_query=state["user_query"],
                attachments=state.get("attachments")
            )
            messages.append(user_message)

            # 確保 SystemMessage 在最前面（相容所有 LLM 後端）
            messages = ensure_system_message_first(messages)

            # 呼叫 LLM（異步）
            response = await llm.ainvoke(messages)
            response_text = extract_text_content(response.content)

            logger.debug(
                f"Base Graph LLM 回應完成",
                extra={
                    "user_query_length": len(state["user_query"]),
                    "response_length": len(response_text),
                    "has_attachments": bool(state.get("attachments"))
                }
            )

            return {
                **state,
                "final_response": response_text
            }

        except Exception as e:
            # 捕獲並記錄錯誤
            logger.error(
                f"Base Graph LLM 節點執行失敗: {e}",
                extra={
                    "user_query": state["user_query"][:100],
                    "error_type": type(e).__name__,
                    "has_attachments": bool(state.get("attachments"))
                },
                exc_info=True
            )
            # 重新拋出異常，讓 executor 處理
            raise

    # 建立 Graph
    graph = StateGraph(BaseGraphState)

    # 新增節點
    graph.add_node("llm", llm_node)

    # 新增邊（使用 START 常數）
    graph.add_edge(START, "llm")
    graph.add_edge("llm", END)

    return graph.compile()


# ============ 主程式 (用於生成流程圖) ============
# 在backend目錄下使用模組方式執行
# uv run python -m app.modules.graphs.definitions.base_graph
if __name__ == "__main__":
    from pathlib import Path
    import sys

    # 添加專案路徑 (backend 目錄)
    # base_graph.py 在: backend/app/modules/graphs/definitions/
    # 需要回到 backend/ 目錄
    backend_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(backend_root))

    from app.core.config import settings
    from app.llm.factory import LLMProviderFactory

    print("=" * 60)
    print("生成 Base Graph 流程圖...")
    print("=" * 60)

    # 建立 LLM Provider (使用設定檔)
    llm_provider = LLMProviderFactory.create_from_settings(settings)
    print(f"[OK] LLM Provider 初始化完成: {type(llm_provider).__name__}")

    # 建立 Graph
    app = create_base_graph(settings, llm_provider)
    print("[OK] Base Graph 建立完成")

    # 生成流程圖並儲存為 PNG
    output_path = Path(__file__).parent / "base_graph.png"

    try:
        # 取得 Mermaid 圖表並轉換為 PNG
        png_data = app.get_graph().draw_mermaid_png()

        with open(output_path, "wb") as f:
            f.write(png_data)

        print(f"[OK] 流程圖已生成: {output_path}")
        print("=" * 60)
    except Exception as e:
        print(f"[ERROR] 生成流程圖失敗: {e}")
        print("提示: 請確保已安裝 graphviz 和相關依賴")
        print("=" * 60)
        sys.exit(1)
