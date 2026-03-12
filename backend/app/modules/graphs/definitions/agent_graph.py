# -*- coding: utf-8 -*-
"""
通用工具 Agent Graph：支援工具調用的 ReAct 循環

流程：START -> agent_node <-> tool_node -> END
Agent 會根據任務自動決定是否使用工具（如程式碼執行），
並在需要時進行多輪工具調用直到完成任務。
"""
from typing import TypedDict, List, Dict, Any, Annotated

try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python < 3.11

from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from loguru import logger

from app.modules.graphs.utils import (
    prepare_multimodal_message,
    ensure_system_message_first,
    extract_text_content,
)
from app.modules.graphs.tools.code_execution import create_execute_python_tool


# ==================== 預設系統提示詞 ====================

AGENT_SYSTEM_PROMPT = """
你是一個具備「自主執行能力」的進階 AI 助理。

【你的超能力與環境】
你的後端已經連接了一個安全的本地端 Docker Sandbox（沙箱環境）。
當你面對需要計算數學、處理資料、分析 RAG 檢索內容，或任何無法僅靠文字推理解決的問題時，你「擁有能力」且「被要求」親自撰寫 Python 程式碼來找出答案。

【嚴格執行守則 - 必須遵守】
1. 絕對禁止「只說不做」：當你需要寫程式時，絕對不可以只在對話中輸出 Markdown 程式碼區塊（```python ... ```）然後等待使用者去執行。使用者無法執行程式碼！
2. 必須呼叫工具：你必須主動呼叫 `execute_python` 工具將程式碼送入沙箱執行。
3. 工作流程：
   - 思考：判斷問題是否需要寫程式解決。
   - 呼叫工具：撰寫純 Python 程式碼，並將其作為參數傳給執行工具。
   - 分析結果：等待沙箱回傳執行結果（stdout/stderr）。如果報錯，你必須自己修正程式碼並重新呼叫工具。
   - 最終回答：根據沙箱回傳的成功結果，用自然語言總結並回答使用者。
4. 輸出要求：傳入工具的程式碼必須包含 `print()` 函數，否則你將無法在沙箱回傳中看到任何結果。

記住：你的任務不是「提供程式碼給使用者」，而是「自己執行程式碼並把最終答案告訴使用者」。
"""


class AgentGraphState(TypedDict):
    """Agent Graph 狀態"""
    messages: Annotated[List[BaseMessage], add_messages]  # 完整訊息歷史（含 tool calls）
    user_query: str                    # 當前使用者問題
    final_response: str                # 最終回應
    iteration_count: int               # 當前迭代次數
    max_iterations: int                # 最大迭代次數
    code_executions: List[Dict[str, Any]]  # 程式碼執行記錄
    attachments: NotRequired[List[Dict[str, Any]]]
    custom_system_prompt: NotRequired[str]


def _build_file_info_prompt(attachments: list) -> str:
    """
    從附件列表中提取 file 類型附件，生成檔案資訊提示詞片段

    Args:
        attachments: Graph 格式的附件列表

    Returns:
        檔案資訊提示詞，若無檔案則返回空字串
    """
    file_attachments = [a for a in attachments if a.get("type") == "file"]
    logger.debug(
        f"檔案附件篩選 | total_attachments={len(attachments)} | "
        f"file_attachments={len(file_attachments)} | "
        f"attachment_types={[a.get('type') for a in attachments]}"
    )
    if not file_attachments:
        return ""

    lines = [
        "\n## 使用者上傳的檔案",
        "以下檔案已放置於 /workspace/input/ 目錄：",
    ]

    for att in file_attachments:
        filename = att.get("original_filename", "unknown")
        metadata = att.get("metadata", {})
        file_size = metadata.get("file_size", 0)
        ext = metadata.get("extension", "")

        # 格式化檔案大小
        if file_size >= 1024 * 1024:
            size_str = f"{file_size / 1024 / 1024:.1f}MB"
        elif file_size >= 1024:
            size_str = f"{file_size / 1024:.1f}KB"
        else:
            size_str = f"{file_size}B"

        lines.append(f"- {filename} ({size_str})")

    lines.append("")
    lines.append("你可以在 Python 程式碼中讀取這些檔案，例如：")

    # 根據檔案類型提供範例程式碼
    has_excel = any(
        a.get("metadata", {}).get("extension") in (".xlsx", ".xls")
        for a in file_attachments
    )
    has_csv = any(
        a.get("metadata", {}).get("extension") == ".csv"
        for a in file_attachments
    )
    has_docx = any(
        a.get("metadata", {}).get("extension") == ".docx"
        for a in file_attachments
    )

    if has_excel:
        excel_file = next(
            a for a in file_attachments
            if a.get("metadata", {}).get("extension") in (".xlsx", ".xls")
        )
        excel_name = excel_file.get("original_filename", "data.xlsx")
        lines.append(f"```python")
        lines.append(f"import pandas as pd")
        lines.append(f"df = pd.read_excel('/workspace/input/{excel_name}')")
        lines.append(f"print(df.head())")
        lines.append(f"```")

    if has_csv:
        csv_file = next(
            a for a in file_attachments
            if a.get("metadata", {}).get("extension") == ".csv"
        )
        csv_name = csv_file.get("original_filename", "data.csv")
        lines.append(f"```python")
        lines.append(f"import pandas as pd")
        lines.append(f"df = pd.read_csv('/workspace/input/{csv_name}')")
        lines.append(f"print(df.head())")
        lines.append(f"```")

    if has_docx:
        docx_file = next(
            a for a in file_attachments
            if a.get("metadata", {}).get("extension") == ".docx"
        )
        docx_name = docx_file.get("original_filename", "document.docx")
        lines.append(f"```python")
        lines.append(f"from docx import Document")
        lines.append(f"doc = Document('/workspace/input/{docx_name}')")
        lines.append(f"for para in doc.paragraphs:")
        lines.append(f"    print(para.text)")
        lines.append(f"```")
        lines.append(f"")
        lines.append(f"若需要修改或建立 Word 文件，將結果儲存到 /workspace/output/：")
        lines.append(f"```python")
        lines.append(f"from docx import Document")
        lines.append(f"doc = Document('/workspace/input/{docx_name}')  # 或 Document() 建立新文件")
        lines.append(f"doc.add_heading('標題', level=1)")
        lines.append(f"doc.add_paragraph('內容文字')")
        lines.append(f"doc.save('/workspace/output/result.docx')")
        lines.append(f"print('文件已儲存到 /workspace/output/result.docx')")
        lines.append(f"```")

    return "\n".join(lines)


def create_agent_graph(settings, llm_provider, sandbox_service) -> CompiledStateGraph:
    """
    建立通用工具 Agent Graph

    Args:
        settings: 應用設定物件（來自 core.config）
        llm_provider: LLM Provider 實例
        sandbox_service: SandboxService 實例

    Returns:
        CompiledStateGraph: 編譯後的 Graph
    """
    # 取得 LangChain LLM 實例
    llm = llm_provider.to_langchain_llm()

    # 建立工具列表
    execute_python = create_execute_python_tool(sandbox_service)
    tools = [execute_python]

    # 將工具綁定到 LLM
    llm_with_tools = llm.bind_tools(tools)

    # 建立 ToolNode
    tool_node = ToolNode(tools)

    # ==================== 節點定義 ====================

    async def agent_node(state: AgentGraphState) -> dict:
        """
        Agent 節點：呼叫 LLM，可能產生 tool_calls

        首次呼叫時會加入系統提示詞和使用者訊息，並將它們持久化到 state；
        後續循環中依賴 state 中已有的完整訊息歷史（含 tool results）。
        """
        messages = list(state["messages"])
        new_messages_for_state = []

        # 首次執行：加入系統提示詞和使用者訊息
        if state["iteration_count"] == 0:
            # 系統提示詞
            system_prompt = state.get("custom_system_prompt") or AGENT_SYSTEM_PROMPT

            # 如果有上傳的檔案附件，動態注入檔案資訊到系統提示詞
            attachments = state.get("attachments") or []
            file_info_prompt = _build_file_info_prompt(attachments)
            if file_info_prompt:
                system_prompt = system_prompt + "\n" + file_info_prompt

            system_msg = SystemMessage(content=system_prompt)
            messages.insert(0, system_msg)
            new_messages_for_state.append(system_msg)

            # 使用者訊息（支援多模態）
            user_message = prepare_multimodal_message(
                user_query=state["user_query"],
                attachments=attachments,
            )
            messages.append(user_message)
            new_messages_for_state.append(user_message)
        else:
            # 後續迭代：add_messages reducer 可能將 SystemMessage 附加到歷史訊息之後，
            # 導致部分 LLM（如 Qwen3.5）因 system message 不在開頭而報錯，
            # 因此需要重新排列確保 SystemMessage 在最前面
            messages = ensure_system_message_first(messages)

        # 診斷日誌：記錄送給 LLM 的訊息摘要
        logger.debug(
            f"Agent 送出訊息 | message_count={len(messages)} | "
            f"types={[type(m).__name__ for m in messages]} | "
            f"system_prompt_length={len(messages[0].content) if messages else 0} | "
            f"attachments_count={len(state.get('attachments') or [])}"
        )

        # 呼叫 LLM（異步），含 MALFORMED_FUNCTION_CALL 重試
        max_retries = 3
        for attempt in range(max_retries):
            response = await llm_with_tools.ainvoke(messages)

            # 檢查是否為空回應（無內容且無 tool_calls）
            has_content = bool(response.content)
            has_tool_calls = bool(response.tool_calls)

            if has_content or has_tool_calls or attempt == max_retries - 1:
                break

            # 取得 finish_reason 以判斷失敗原因
            finish_reason = response.response_metadata.get("finish_reason", "")

            logger.warning(
                f"Agent LLM 返回空回應，重試中 | "
                f"attempt={attempt + 1}/{max_retries} | "
                f"finish_reason={finish_reason} | "
                f"response_metadata={response.response_metadata}"
            )

            # 針對 MALFORMED_FUNCTION_CALL：加入引導訊息幫助模型修正
            if finish_reason == "MALFORMED_FUNCTION_CALL":
                from langchain_core.messages import HumanMessage as HM
                guidance = HM(content=(
                    "（系統提示：你剛才的工具呼叫格式有誤。"
                    "請使用 execute_python 工具，只需傳入一個 `code` 參數，"
                    "值為完整的 Python 程式碼字串。"
                    "請將所有程式碼寫在同一個 code 參數中，不要拆分成多個參數。）"
                ))
                messages.append(guidance)

        new_messages_for_state.append(response)

        # 更新迭代計數
        new_iteration = state["iteration_count"] + 1

        tool_calls = response.tool_calls or []
        text_content = extract_text_content(response.content)
        content_preview = (text_content[:100] + "...") if len(text_content) > 100 else text_content
        logger.info(
            f"Agent 節點完成 | iteration={new_iteration} | "
            f"has_tool_calls={bool(tool_calls)} | "
            f"tool_calls_count={len(tool_calls)} | "
            f"tool_names={[tc.get('name') for tc in tool_calls]} | "
            f"content_preview={content_preview!r} | "
            f"finish_reason={response.response_metadata.get('finish_reason', 'N/A')}"
        )

        return {
            "messages": new_messages_for_state,
            "iteration_count": new_iteration,
        }

    # ==================== 條件邊定義 ====================

    def should_continue(state: AgentGraphState) -> str:
        """決定是否繼續工具調用循環"""
        messages = state["messages"]

        # 取得最後一條訊息
        last_message = messages[-1]

        # 如果不是 AI 訊息，結束
        if not isinstance(last_message, AIMessage):
            return "end"

        # 如果有 tool_calls 且未超過最大迭代次數，繼續
        if last_message.tool_calls and state["iteration_count"] < state["max_iterations"]:
            return "tools"

        # 如果超過最大迭代次數，記錄警告
        if last_message.tool_calls and state["iteration_count"] >= state["max_iterations"]:
            logger.warning(
                f"Agent 達到最大迭代次數 ({state['max_iterations']})，強制結束",
                extra={"user_query": state["user_query"][:100]},
            )

        return "end"

    async def finalize_node(state: AgentGraphState) -> dict:
        """
        結束節點：提取最終回應
        """
        messages = state["messages"]

        # 從最後一條 AI 訊息提取回應
        final_response = ""
        for msg in reversed(messages):
            text = extract_text_content(msg.content) if isinstance(msg, AIMessage) else ""
            if text and not msg.tool_calls:
                final_response = text
                break

        # 如果沒有找到純文字回應（所有 AI 訊息都是 tool_calls），使用最後一條
        if not final_response:
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    text = extract_text_content(msg.content)
                    if text:
                        final_response = text
                        break

        return {
            "final_response": final_response,
        }

    # ==================== 組裝 Graph ====================

    graph = StateGraph(AgentGraphState)

    # 新增節點
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("finalize", finalize_node)

    # 新增邊
    graph.add_edge(START, "agent")

    # Agent 節點的條件邊
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",   # 有 tool_calls -> 執行工具
            "end": "finalize",  # 沒有 tool_calls -> 結束
        },
    )

    # 工具執行完畢 -> 回到 Agent 節點
    graph.add_edge("tools", "agent")

    # 結束節點 -> END
    graph.add_edge("finalize", END)

    return graph.compile()


# ============ 主程式 (用於生成流程圖) ============
# 在backend目錄下使用模組方式執行
# uv run python -m app.modules.graphs.definitions.agent_graph
if __name__ == "__main__":
    from pathlib import Path
    import sys

    backend_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(backend_root))

    from app.core.config import settings
    from app.llm.factory import LLMProviderFactory
    from app.modules.sandbox.service import SandboxService

    print("=" * 60)
    print("生成 Agent Graph 流程圖...")
    print("=" * 60)

    llm_provider = LLMProviderFactory.create_from_settings(settings)
    print(f"[OK] LLM Provider 初始化完成: {type(llm_provider).__name__}")

    sandbox_service = SandboxService(settings)
    print("[OK] SandboxService 建立完成")

    app = create_agent_graph(settings, llm_provider, sandbox_service)
    print("[OK] Agent Graph 建立完成")

    output_path = Path(__file__).parent / "agent_graph.png"

    try:
        png_data = app.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"[OK] 流程圖已生成: {output_path}")
        print("=" * 60)
    except Exception as e:
        print(f"[ERROR] 生成流程圖失敗: {e}")
        print("=" * 60)
        sys.exit(1)
