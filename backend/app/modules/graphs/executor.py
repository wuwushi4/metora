# -*- coding: utf-8 -*-
"""
Graph 執行器：統一執行 Graph 並管理對話記憶
"""
import asyncio
from typing import Dict, Any, List, AsyncGenerator, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AIMessageChunk, ToolMessage
from loguru import logger

from app.modules.graphs.registry import GraphRegistry
from app.modules.graphs.utils import extract_text_content


class GraphExecutor:
    """Graph 執行器：統一執行 Graph 並管理對話記憶"""

    def __init__(self, graph_type: str, settings):
        """
        初始化 Graph 執行器

        Args:
            graph_type: Graph 類型
            settings: 應用設定物件
        """
        self.graph_type = graph_type
        self.settings = settings
        self.graph = GraphRegistry.get(graph_type)

    @staticmethod
    def _get_friendly_error_message(e: Exception) -> str:
        """將 LLM 異常轉換為使用者友善的錯誤訊息"""
        error_type = type(e).__name__
        error_str = str(e).lower()

        # 配額 / 速率限制
        if "resourceexhausted" in error_type.lower() or "429" in str(e) or "quota" in error_str:
            return "AI 服務配額已用盡，請稍後再試或聯繫管理員檢查 API 額度"

        # 認證失敗
        if "401" in str(e) or "invalid" in error_str and "key" in error_str:
            return "AI 服務認證失敗，請聯繫管理員檢查 API Key 設定"

        # 權限不足
        if "403" in str(e) or "permissiondenied" in error_type.lower():
            return "AI 服務權限不足，請聯繫管理員檢查 API 存取權限"

        # 連線失敗
        if "connection" in error_str or "timeout" in error_str or "unreachable" in error_str:
            return "無法連線到 AI 服務，請確認服務是否正常運行"

        # 模型不存在
        if "not found" in error_str and "model" in error_str:
            return "指定的 AI 模型不存在，請聯繫管理員檢查模型設定"

        # 預設訊息
        return f"AI 服務發生錯誤（{error_type}），請稍後再試"

    def _prepare_messages(
        self,
        all_messages: List[Dict[str, str]],
        turn_limit: int
    ) -> List[BaseMessage]:
        """
        準備對話歷史

        Args:
            all_messages: 所有訊息列表，格式：[{"role": "user", "content": "..."}, ...]
            turn_limit: 輪數限制（3 或 5）

        Returns:
            最近 N 輪的 BaseMessage 列表
        """
        # 過濾出 user 和 assistant 訊息
        filtered = [m for m in all_messages if m["role"] in ("user", "assistant")]

        # 計算需要取多少條訊息（一輪 = user + assistant = 2條）
        message_limit = turn_limit * 2

        # 取最近 N 輪
        recent_messages = filtered[-message_limit:] if len(filtered) > message_limit else filtered

        # 轉換為 BaseMessage
        langchain_messages = []
        for msg in recent_messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        return langchain_messages

    async def execute(
        self,
        user_query: str,
        history_messages: List[Dict[str, str]],
        collection_ids: List[int] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        執行 Graph（非串流）

        Args:
            user_query: 使用者問題
            history_messages: 歷史訊息
            collection_ids: Collection IDs（僅 RAG Graph 需要）
            attachments: 附件列表（Base64 格式）

        Returns:
            執行結果，包含 final_response 等資訊
        """
        # 準備狀態
        if self.graph_type == "base_graph":
            # 基礎 Graph：使用 5 輪記憶
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS
                ),
                "user_query": user_query,
                "final_response": "",
                "attachments": attachments
            }

        elif self.graph_type == "rag_graph":
            # RAG Graph：區分 5 輪和 3 輪
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS  # 5 輪
                ),
                "rewrite_context": self._prepare_messages(
                    history_messages,
                    self.settings.QUERY_REWRITE_CONTEXT_TURNS  # 3 輪
                ),
                "user_query": user_query,
                "collection_ids": collection_ids or [],
                "need_rag": False,
                "intent_reason": "",
                "sub_queries": [],
                "retrieval_results": [],
                "final_response": "",
                "attachments": attachments
            }

        elif self.graph_type == "regulation_graph":
            # Regulation Graph：法規查詢專用
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS  # 5 輪
                ),
                "rewrite_context": self._prepare_messages(
                    history_messages,
                    self.settings.QUERY_REWRITE_CONTEXT_TURNS  # 3 輪
                ),
                "user_query": user_query,
                "collection_ids": collection_ids or [],
                "attachments": attachments,
                "is_regulation_query": False,
                "query_type": "",
                "intent_reason": "",
                "rewritten_queries": [],
                "target_articles": [],
                "retrieval_results": [],
                "final_response": "",
                "cited_articles": []
            }

        elif self.graph_type == "agent_graph":
            # Agent Graph：通用工具 Agent
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS
                ),
                "user_query": user_query,
                "final_response": "",
                "iteration_count": 0,
                "max_iterations": self.settings.SANDBOX_MAX_ITERATIONS,
                "code_executions": [],
                "attachments": attachments
            }

        else:
            raise ValueError(f"不支援的 Graph 類型: {self.graph_type}")

        # 準備 RunnableConfig（用於傳遞輸入檔案等資訊到工具）
        run_config = {}
        if self.graph_type == "agent_graph" and attachments:
            input_files = [
                {
                    "file_path": a["file_path"],
                    "original_filename": a["original_filename"],
                }
                for a in attachments
                if a.get("type") == "file" and a.get("file_path")
            ]
            if input_files:
                run_config = {"configurable": {"input_files": input_files}}

        # 執行 Graph
        result = await self.graph.ainvoke(
            state,
            config=run_config if run_config else None,
        )

        return result

    async def stream_execute(
        self,
        user_query: str,
        history_messages: List[Dict[str, str]],
        collection_ids: List[int] = None,
        attachments: List[Dict[str, Any]] = None,
        custom_system_prompt: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        執行 Graph（串流）

        Args:
            user_query: 使用者問題
            history_messages: 歷史訊息
            collection_ids: Collection IDs
            attachments: 附件列表（Base64 格式）
            custom_system_prompt: 自訂系統提示詞（優先於預設提示詞）
            timeout: 執行超時時間（秒），預設從 settings 讀取

        Yields:
            字典，包含 type 和 content/data
            - type="node_start": 節點開始執行
            - type="node_end": 節點執行完成
            - type="metadata": 中間節點資訊
            - type="token": LLM token 串流（逐字輸出）
            - type="done": 執行完成
            - type="error": 執行錯誤（包含超時）
        """
        # 準備狀態
        if self.graph_type == "base_graph":
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS
                ),
                "user_query": user_query,
                "final_response": "",
                "attachments": attachments,
                "custom_system_prompt": custom_system_prompt
            }

        elif self.graph_type == "rag_graph":
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS
                ),
                "rewrite_context": self._prepare_messages(
                    history_messages,
                    self.settings.QUERY_REWRITE_CONTEXT_TURNS
                ),
                "user_query": user_query,
                "collection_ids": collection_ids or [],
                "need_rag": False,
                "intent_reason": "",
                "sub_queries": [],
                "retrieval_results": [],
                "final_response": "",
                "attachments": attachments,
                "custom_system_prompt": custom_system_prompt
            }

        elif self.graph_type == "regulation_graph":
            # Regulation Graph：法規查詢專用
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS  # 5 輪
                ),
                "rewrite_context": self._prepare_messages(
                    history_messages,
                    self.settings.QUERY_REWRITE_CONTEXT_TURNS  # 3 輪
                ),
                "user_query": user_query,
                "collection_ids": collection_ids or [],
                "attachments": attachments,
                "is_regulation_query": False,
                "query_type": "",
                "intent_reason": "",
                "rewritten_queries": [],
                "target_articles": [],
                "retrieval_results": [],
                "final_response": "",
                "cited_articles": [],
                "custom_system_prompt": custom_system_prompt
            }

        elif self.graph_type == "agent_graph":
            # Agent Graph：通用工具 Agent
            state = {
                "messages": self._prepare_messages(
                    history_messages,
                    self.settings.GRAPH_MEMORY_TURNS
                ),
                "user_query": user_query,
                "final_response": "",
                "iteration_count": 0,
                "max_iterations": self.settings.SANDBOX_MAX_ITERATIONS,
                "code_executions": [],
                "attachments": attachments,
                "custom_system_prompt": custom_system_prompt
            }

        else:
            raise ValueError(f"不支援的 Graph 類型: {self.graph_type}")

        # 使用配置的預設超時時間
        execution_timeout = timeout or self.settings.GRAPH_EXECUTION_TIMEOUT

        # 準備 RunnableConfig（用於傳遞輸入檔案等資訊到工具）
        run_config = {}
        if self.graph_type == "agent_graph" and attachments:
            input_files = [
                {
                    "file_path": a["file_path"],
                    "original_filename": a["original_filename"],
                }
                for a in attachments
                if a.get("type") == "file" and a.get("file_path")
            ]
            if input_files:
                run_config = {"configurable": {"input_files": input_files}}

        try:
            # 使用 asyncio.timeout 包裝整個執行
            async with asyncio.timeout(execution_timeout):
                # 使用混合串流模式
                async for stream_mode, chunk in self.graph.astream(
                    state,
                    config=run_config if run_config else None,
                    stream_mode=["updates", "messages"]
                ):
                    # ==================== 處理 updates 模式（節點完成事件）====================
                    if stream_mode == "updates":
                        for node_name, node_output in chunk.items():
                            # 發送節點開始事件
                            yield {
                                "type": "node_start",
                                "node": node_name
                            }

                            # 處理不同節點的輸出
                            # ========== RAG Graph 節點 ==========
                            if node_name == "intent_check":
                                # 意圖判別完成
                                yield {
                                    "type": "metadata",
                                    "step": "intent_check",
                                    "data": {
                                        "need_rag": node_output.get("need_rag"),
                                        "intent_reason": node_output.get("intent_reason")
                                    }
                                }

                            elif node_name == "query_rewrite":
                                # 查詢重構完成（RAG Graph 和 Regulation Graph 共用節點名）
                                if self.graph_type == "rag_graph":
                                    # RAG Graph: 返回 sub_queries
                                    yield {
                                        "type": "metadata",
                                        "step": "query_rewrite",
                                        "data": {
                                            "sub_queries": node_output.get("sub_queries", [])
                                        }
                                    }
                                elif self.graph_type == "regulation_graph":
                                    # Regulation Graph: 返回 target_articles 和 rewritten_queries
                                    yield {
                                        "type": "metadata",
                                        "step": "query_rewrite",
                                        "data": {
                                            "target_articles": node_output.get("target_articles", []),
                                            "rewritten_queries": node_output.get("rewritten_queries", [])
                                        }
                                    }

                            elif node_name == "rag_retrieval":
                                # 檢索完成
                                retrieval_results = node_output.get("retrieval_results", [])
                                yield {
                                    "type": "metadata",
                                    "step": "rag_retrieval",
                                    "data": {
                                        "results_count": len(retrieval_results),
                                        "retrieval_results": retrieval_results
                                    }
                                }

                            # ========== Regulation Graph 節點 ==========
                            elif node_name == "intent_analysis":
                                # 意圖分析完成
                                yield {
                                    "type": "metadata",
                                    "step": "intent_analysis",
                                    "data": {
                                        "is_regulation_query": node_output.get("is_regulation_query"),
                                        "query_type": node_output.get("query_type"),
                                        "intent_reason": node_output.get("intent_reason")
                                    }
                                }

                            elif node_name == "regulation_search":
                                # 法規檢索完成
                                retrieval_results = node_output.get("retrieval_results", [])
                                yield {
                                    "type": "metadata",
                                    "step": "regulation_search",
                                    "data": {
                                        "results_count": len(retrieval_results),
                                        "retrieval_results": retrieval_results
                                    }
                                }

                            # ========== Agent Graph 節點 ==========
                            elif node_name == "agent" and self.graph_type == "agent_graph":
                                # Agent 節點完成：檢查是否有 tool_calls
                                messages = node_output.get("messages", [])
                                for msg in messages:
                                    if isinstance(msg, AIMessage) and msg.tool_calls:
                                        for tc in msg.tool_calls:
                                            yield {
                                                "type": "tool_call",
                                                "data": {
                                                    "tool_name": tc.get("name", ""),
                                                    "tool_call_id": tc.get("id", ""),
                                                    "args": tc.get("args", {}),
                                                }
                                            }

                            elif node_name == "tools" and self.graph_type == "agent_graph":
                                # 工具節點完成：返回執行結果
                                messages = node_output.get("messages", [])
                                for msg in messages:
                                    if isinstance(msg, ToolMessage):
                                        output_files = []
                                        if isinstance(msg.artifact, dict):
                                            output_files = msg.artifact.get("output_files", []) or []

                                        yield {
                                            "type": "tool_result",
                                            "data": {
                                                "tool_name": msg.name or "",
                                                "content": msg.content[:5000] if msg.content else "",
                                                "output_files": output_files,
                                            }
                                        }

                            # ==================== 已停用：reference_expansion 節點處理 ====================
                            # elif node_name == "reference_expansion":
                            #     # 引用擴展完成
                            #     related_articles = node_output.get("related_articles", [])
                            #     yield {
                            #         "type": "metadata",
                            #         "step": "reference_expansion",
                            #         "data": {
                            #             "related_count": len(related_articles),
                            #             "related_articles": related_articles
                            #         }
                            #     }
                            # ==================== 已停用結束 ====================

                            # 發送節點結束事件
                            yield {
                                "type": "node_end",
                                "node": node_name
                            }

                    # ==================== 處理 messages 模式（LLM token 串流）====================
                    elif stream_mode == "messages":
                        message_chunk, metadata = chunk
                        current_node = metadata.get("langgraph_node")

                        # ========== Agent Graph：agent 節點的 token 串流 ==========
                        # tool_call 和 tool_result 在 updates 模式中完整處理
                        if self.graph_type == "agent_graph" and current_node == "agent":
                            if isinstance(message_chunk, AIMessageChunk) and message_chunk.content:
                                text = extract_text_content(message_chunk.content)
                                if text:
                                    yield {
                                        "type": "token",
                                        "content": text
                                    }

                        # ========== Agent Graph：finalize 節點的 token 不需要串流 ==========
                        elif self.graph_type == "agent_graph" and current_node in ("tools", "finalize"):
                            pass  # 工具結果和結束節點由 updates 模式處理

                        # ========== 其他 Graph 的 token 串流（原有邏輯）==========
                        # base_graph: "llm"
                        # rag_graph: "llm_final"
                        # regulation_graph: "response_generation"
                        elif current_node in ("llm_final", "llm", "response_generation"):
                            # 過濾：只串流新生成的 AI token，忽略歷史訊息
                            if isinstance(message_chunk, AIMessageChunk) and message_chunk.content:
                                text = extract_text_content(message_chunk.content)
                                if text:
                                    yield {
                                        "type": "token",
                                        "content": text
                                    }

            # 發送完成訊號
            yield {"type": "done"}

        except asyncio.TimeoutError:
            # Graph 執行超時
            logger.error(
                f"Graph 執行超時 ({execution_timeout}s)",
                extra={
                    "graph_type": self.graph_type,
                    "user_query": user_query[:100],  # 只記錄前100字元
                    "timeout": execution_timeout
                }
            )
            yield {
                "type": "error",
                "content": f"AI 回應超時（超過 {execution_timeout} 秒），請稍後再試或簡化問題"
            }

        except Exception as e:
            # 一般異常（LLM 連線失敗、API 錯誤、配額不足等）
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(
                f"Graph 執行失敗: {error_type} - {error_msg}",
                extra={
                    "graph_type": self.graph_type,
                    "user_query": user_query[:100],
                    "error_type": error_type
                },
                exc_info=True
            )

            # 將常見 LLM 錯誤轉換為使用者友善訊息
            friendly_msg = self._get_friendly_error_message(e)
            yield {
                "type": "error",
                "content": friendly_msg
            }
