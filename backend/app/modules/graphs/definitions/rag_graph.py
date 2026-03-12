# -*- coding: utf-8 -*-
"""
可以執行 RAG 的 Graph
流程：START -> intent_check -> (需要RAG) -> query_rewrite -> rag_retrieval -> llm_final -> END
                            -> (不需要RAG) -> llm_final -> END
"""
from typing import TypedDict, List, Dict, Any
try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python < 3.11

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.modules.graphs.utils import (
    prepare_multimodal_message,
    parse_json_with_fallback,
    format_retrieval_results,
    extract_text_content,
)


class RAGGraphState(TypedDict):
    """RAG Graph 狀態"""
    # 對話歷史
    messages: List[BaseMessage]       # 完整對話歷史（最近 5 輪，用於最終回應）
    rewrite_context: List[BaseMessage] # 查詢重構用上下文（最近 3 輪）

    # 使用者輸入
    user_query: str                   # 當前使用者問題
    collection_ids: List[int]         # 選定的 Collections
    attachments: NotRequired[List[Dict[str, Any]]]  # 附件列表（Base64 格式）- 非必需欄位

    # 中間狀態
    need_rag: bool                    # 是否需要 RAG
    intent_reason: str                # 意圖判別理由
    sub_queries: List[Dict[str, str]] # 拆解並重寫後的子問題
    retrieval_results: List[Dict[str, Any]]  # 檢索結果

    # 最終輸出
    final_response: str               # 最終回應

    # 自訂提示詞
    custom_system_prompt: NotRequired[str]  # 自訂系統提示詞 - 非必需欄位


def create_rag_graph(settings, llm_provider, retrieval_service) -> CompiledStateGraph:
    """
    建立 RAG Graph

    Args:
        settings: 應用設定物件（來自 core.config）
        llm_provider: LLM Provider 實例
        retrieval_service: RetrievalService 實例

    Returns:
        CompiledStateGraph: 編譯後的 Graph

    注意：
        - 符合 LangGraph 1.0 最佳實踐
        - 使用輔助函數消除代碼重複
        - 支援多模態輸入（文字 + 圖片）
    """
    # 取得 LangChain LLM 實例
    llm = llm_provider.to_langchain_llm()

    # ==================== 節點定義 ====================

    async def intent_check_node(state: RAGGraphState) -> RAGGraphState:
        """
        意圖判別節點：判斷是否需要進入 RAG 檢索流程（異步）

        使用最近 3 輪對話作為上下文，支援多模態輸入。
        """
        # 構建系統提示
        system_prompt = """你是一個意圖分析專家。請分析使用者的問題，判斷是否需要查詢知識庫。

判斷標準：
1. 需要 RAG (need_rag=true)：
   - 詢問專業知識、文件內容、技術細節
   - 需要引用具體資料或文獻
   - 與特定領域相關的深入問題

2. 不需要 RAG (need_rag=false)：
   - 問候、閒聊、感謝等社交對話
   - 常識性問題（如：天空為什麼是藍色）
   - 簡單的數學計算
   - 關於你自己的問題（如：你是誰、你能做什麼）

請以 JSON 格式回答：
{
    "need_rag": true/false,
    "reason": "判斷理由說明"
}
"""

        # 準備訊息（最近 3 輪對話）
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["rewrite_context"])

        # 使用輔助函數準備使用者訊息（支援多模態）
        user_message = prepare_multimodal_message(
            user_query=state["user_query"],
            attachments=state.get("attachments"),
            message_prefix="使用者問題："
        )
        messages.append(user_message)

        # 呼叫 LLM（異步）
        response = await llm.ainvoke(messages)

        # 使用輔助函數解析 JSON 回應
        fallback_value = {
            "need_rag": True,
            "reason": "無法解析意圖，預設進入 RAG 流程"
        }
        result, success = parse_json_with_fallback(
            response_content=extract_text_content(response.content),
            fallback_value=fallback_value,
            context="意圖判別",
            user_query=state["user_query"]
        )

        need_rag = result.get("need_rag", True)
        reason = result.get("reason", "")

        return {
            **state,
            "need_rag": need_rag,
            "intent_reason": reason
        }

    async def query_decompose_rewrite_node(state: RAGGraphState) -> RAGGraphState:
        """
        查詢重構節點：（異步）
        1. 拆解複雜問題為多個子問題
        2. 重寫每個子問題為檢索友好的形式

        使用最近 3 輪對話作為上下文，支援多模態輸入。
        """
        system_prompt = """你是一個查詢優化專家。請執行以下任務：

任務 1：問題拆解
- 如果使用者問題包含多個獨立的子問題，請將其拆解
- 如果是簡單問題，保持原樣不拆分
- 每個子問題應該是可以獨立檢索的

任務 2：查詢重寫
- 將每個子問題改寫為更適合檢索的形式
- 加入關鍵字、消除歧義、補充必要的上下文
- 使用明確的術語，避免代詞（如：這個、那個）

請以 JSON 格式回答：
{
    "sub_queries": [
        {
            "original": "原始子問題",
            "rewritten": "重寫後的檢索查詢"
        },
        ...
    ]
}

範例：
使用者問題：「剛才提到的那個模型的參數設定是什麼？」
對話上下文：上一輪提到了 BERT 模型

輸出：
{
    "sub_queries": [
        {
            "original": "剛才提到的那個模型的參數設定是什麼？",
            "rewritten": "BERT 模型的超參數配置和訓練參數設定"
        }
    ]
}
"""

        # 準備訊息（最近 3 輪對話）
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["rewrite_context"])

        # 使用輔助函數準備使用者訊息（支援多模態）
        user_message = prepare_multimodal_message(
            user_query=state["user_query"],
            attachments=state.get("attachments"),
            message_prefix="使用者問題："
        )
        messages.append(user_message)

        # 呼叫 LLM（異步）
        response = await llm.ainvoke(messages)

        # 使用輔助函數解析 JSON 回應
        fallback_value = {
            "sub_queries": [{
                "original": state["user_query"],
                "rewritten": state["user_query"]
            }]
        }
        result, success = parse_json_with_fallback(
            response_content=extract_text_content(response.content),
            fallback_value=fallback_value,
            context="查詢重構",
            user_query=state["user_query"]
        )

        sub_queries = result.get("sub_queries", fallback_value["sub_queries"])

        return {
            **state,
            "sub_queries": sub_queries
        }

    async def rag_retrieval_node(state: RAGGraphState) -> RAGGraphState:
        """
        RAG 檢索節點：
        並行檢索所有子問題 × 所有 Collections，合併並重排序結果
        """
        # 準備查詢列表（使用重寫後的查詢）
        queries = [sq["rewritten"] for sq in state["sub_queries"]]

        # 呼叫 RetrievalService 進行檢索
        documents = await retrieval_service.cross_collection_search(
            queries=queries,
            collection_ids=state["collection_ids"],
            top_k=settings.RAG_RETRIEVER_TOP_K,  # 每個查詢取前 RAG_RETRIEVER_TOP_K 個結果
        )

        # 將 Document 對象轉換為字典格式
        results = [doc.to_dict() for doc in documents]

        return {
            **state,
            "retrieval_results": results
        }

    async def llm_final_node(state: RAGGraphState) -> RAGGraphState:
        """
        LLM 最終回應節點：（異步）

        基於檢索結果（如有）和最近 N 輪對話歷史生成最終回應，
        N 由 settings.GRAPH_MEMORY_TURNS 決定。支援多模態輸入，支援自訂提示詞。
        """
        # 判斷是否有檢索結果
        has_retrieval = state.get("retrieval_results") and len(state["retrieval_results"]) > 0

        # 構建系統提示詞
        if state.get("custom_system_prompt"):
            # 使用自訂提示詞作為基礎
            system_prompt = state["custom_system_prompt"]

            # 如果有檢索結果，附加到自訂提示詞後面
            if has_retrieval:
                formatted_results = format_retrieval_results(
                    results=state["retrieval_results"],
                    include_scores=True
                )
                system_prompt += f"\n\n---\n\n檢索到的知識：\n{formatted_results}"
        else:
            # 使用預設提示詞
            if has_retrieval:
                # 有檢索結果 - 使用輔助函數格式化
                system_prompt = """你是一個專業的助手。請基於以下檢索到的知識回答使用者問題。

重要規則：
1. 優先使用檢索結果中的資訊
2. 如果檢索結果與問題不相關，請誠實說明並基於常識回答
3. 引用資訊時可以提及來源（如：根據文件 XXX）
4. 用繁體中文回答，語氣專業友善
5. 回答要結構化、清晰易懂

檢索到的知識：
"""
                # 使用輔助函數格式化檢索結果
                formatted_results = format_retrieval_results(
                    results=state["retrieval_results"],
                    include_scores=True
                )
                system_prompt += formatted_results
            else:
                # 無檢索結果（直接對話）
                system_prompt = """你是一個專業的助手。請基於對話歷史回答使用者問題。

重要規則：
1. 用繁體中文回答，語氣專業友善
2. 如果不確定答案，請誠實說明
3. 回答要結構化、清晰易懂
"""

        # 準備訊息（最近 N 輪對話）
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["messages"])

        # 使用輔助函數準備使用者訊息（支援多模態）
        user_message = prepare_multimodal_message(
            user_query=state["user_query"],
            attachments=state.get("attachments")
        )
        messages.append(user_message)

        # 呼叫 LLM（異步）
        response = await llm.ainvoke(messages)

        return {
            **state,
            "final_response": extract_text_content(response.content)
        }

    # ==================== 條件邊定義 ====================

    def should_retrieve(state: RAGGraphState) -> str:
        """決定是否進入 RAG 檢索流程"""
        return "retrieve" if state["need_rag"] else "final"

    # ==================== 組裝 Graph ====================

    # 建立 Graph
    graph = StateGraph(RAGGraphState)

    # 新增節點
    graph.add_node("intent_check", intent_check_node)
    graph.add_node("query_rewrite", query_decompose_rewrite_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("llm_final", llm_final_node)

    # 新增邊（使用 START 常數）
    graph.add_edge(START, "intent_check")

    # 新增條件邊
    graph.add_conditional_edges(
        "intent_check",
        should_retrieve,
        {
            "retrieve": "query_rewrite",  # 需要 RAG
            "final": "llm_final"          # 不需要 RAG
        }
    )

    # 新增固定邊
    graph.add_edge("query_rewrite", "rag_retrieval")
    graph.add_edge("rag_retrieval", "llm_final")
    graph.add_edge("llm_final", END)

    return graph.compile()


# ============ 主程式 (用於生成流程圖) ============
# 在backend目錄下使用模組方式執行
# uv run python -m app.modules.graphs.definitions.rag_graph
if __name__ == "__main__":
    from pathlib import Path
    import sys
    import asyncio

    # Windows 平台修正
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 添加專案路徑 (backend 目錄)
    # rag_graph.py 在: backend/app/modules/graphs/definitions/
    # 需要回到 backend/ 目錄
    backend_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(backend_root))

    from app.core.config import settings
    from app.llm.factory import LLMProviderFactory
    from app.core.resource_manager import get_resource_manager

    print("=" * 60)
    print("生成 RAG Graph 流程圖...")
    print("=" * 60)

    async def main():
        # 初始化 ResourceManager (需要 RetrievalService)
        rm = get_resource_manager()
        print("[INFO] 正在初始化系統資源 (需要載入 AI 模型)...")
        await rm.initialize()

        # 建立 LLM Provider
        llm_provider = rm.llm_provider
        print(f"[OK] LLM Provider 初始化完成: {type(llm_provider).__name__}")

        # 建立 RetrievalService
        from app.modules.retrieval.service import RetrievalService
        retrieval_service = RetrievalService(hybrid_retriever=rm.hybrid_retriever)
        print("[OK] RetrievalService 建立完成")

        # 建立 Graph
        app = create_rag_graph(settings, llm_provider, retrieval_service)
        print("[OK] RAG Graph 建立完成")

        # 生成流程圖並儲存為 PNG
        output_path = Path(__file__).parent / "rag_graph.png"

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
        finally:
            # 清理資源
            await rm.cleanup()

    # 執行
    asyncio.run(main())
