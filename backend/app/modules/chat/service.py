# -*- coding: utf-8 -*-
"""
聊天服務：管理 Session 和訊息，執行 Graph
"""
from typing import List, Optional, AsyncGenerator, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, timezone
import time
from loguru import logger

from app.db.models.chat_session import ChatSession
from app.db.models.chat_message import ChatMessage
from app.db.models.message_feedback import MessageFeedback
from app.db.models.message_attachment import MessageAttachment
from app.modules.graphs.executor import GraphExecutor
from app.modules.graphs.registry import GraphRegistry
from app.modules.chat.cache import ChatCacheService
from app.modules.chat.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    MessageResponse,
    MessageChunk,
)
from app.modules.feedback.schemas import FeedbackResponse
from app.utils.response import success_response, paginated_response, ApiResponse, PaginatedResponse
from app.utils.exceptions import ResourceNotFoundError, ValidationError


class ChatService:
    """聊天服務：管理 Session 和訊息，執行 Graph"""

    def __init__(
        self,
        db: AsyncSession,
        cache: ChatCacheService,
        settings,
        attachment_converter
    ):
        self.db = db
        self.cache = cache
        self.settings = settings
        self.attachment_converter = attachment_converter

    # ==================== Session 管理 ====================

    async def create_session(
        self,
        user_id: int,
        request: SessionCreateRequest
    ) -> ApiResponse[SessionResponse]:
        """建立新 Session"""
        # 驗證 Graph 是否存在
        if not GraphRegistry.exists(request.graph_type):
            raise ValidationError(f"Graph '{request.graph_type}' 不存在")

        # 生成預設標題
        if request.title:
            title = request.title
        else:
            title = f"新對話 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # 建立資料庫記錄
        session = ChatSession(
            user_id=user_id,
            title=title,
            graph_type=request.graph_type,
            collection_ids=request.collection_ids,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # 嘗試快取 metadata（失敗不影響業務流程）
        try:
            await self.cache.save_metadata(
                session_id=str(session.id),
                metadata={
                    "title": title,
                    "graph_type": request.graph_type,
                    "collection_ids": request.collection_ids,
                    "updated_at": session.updated_at.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"快取 metadata 失敗（已忽略）: {e}")

        return success_response(
            data=SessionResponse.from_orm(session),
            message="Session 建立成功"
        )

    async def get_sessions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> ApiResponse[PaginatedResponse[SessionResponse]]:
        """取得使用者的 Sessions（分頁）"""
        query = select(ChatSession).where(ChatSession.user_id == user_id)

        if is_active is not None:
            query = query.where(ChatSession.is_active == is_active)

        # 計算總數
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # 分頁查詢
        query = query.order_by(desc(ChatSession.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return paginated_response(
            items=[SessionResponse.from_orm(s) for s in sessions],
            total=total or 0,
            page=page,
            page_size=page_size,
            message="Sessions 獲取成功"
        )

    async def get_session_by_id(
        self,
        session_id: UUID,
        user_id: int
    ) -> ApiResponse[SessionResponse]:
        """取得 Session 詳情"""
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise ResourceNotFoundError("Session", str(session_id))

        return success_response(
            data=SessionResponse.from_orm(session),
            message="Session 獲取成功"
        )

    async def update_session(
        self,
        session_id: UUID,
        user_id: int,
        request: SessionUpdateRequest
    ) -> ApiResponse[SessionResponse]:
        """更新 Session"""
        session = await self._get_session_or_404(session_id, user_id)

        if request.title:
            session.title = request.title

        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)

        # 嘗試更新快取（失敗不影響業務流程）
        try:
            await self.cache.save_metadata(
                session_id=str(session_id),
                metadata={
                    "title": session.title,
                    "graph_type": session.graph_type,
                    "collection_ids": session.collection_ids,
                    "updated_at": session.updated_at.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"更新快取 metadata 失敗（已忽略）: {e}")

        return success_response(
            data=SessionResponse.from_orm(session),
            message="Session 更新成功"
        )

    async def delete_session(
        self,
        session_id: UUID,
        user_id: int
    ):
        """刪除 Session（軟刪除）"""
        session = await self._get_session_or_404(session_id, user_id)

        # 軟刪除
        session.is_active = False
        session.updated_at = datetime.utcnow()
        await self.db.commit()

        # 清除快取
        await self.cache.delete_session(str(session_id))

    async def search_sessions(
        self,
        user_id: int,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> ApiResponse[PaginatedResponse[SessionResponse]]:
        """
        搜尋使用者的對話記錄

        搜尋範圍:
        - Session 標題 (ILIKE 模糊匹配)
        - Message 內容 (ILIKE 模糊匹配)

        限制條件:
        - 僅搜尋當前使用者的對話
        - 僅搜尋啟用的 Session

        排序: 匹配數量 DESC -> 更新時間 DESC

        Args:
            user_id: 使用者 ID
            keyword: 搜尋關鍵字
            page: 頁碼
            page_size: 每頁數量

        Returns:
            分頁的搜尋結果
        """
        from datetime import timedelta
        from sqlalchemy.exc import SQLAlchemyError
        from app.utils.exceptions import DatabaseError, AppException

        start_time = time.time()

        logger.info(
            "使用者搜尋對話",
            extra={
                "user_id": user_id,
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            }
        )

        try:
            # 關鍵字預處理 (SQLAlchemy 會自動處理參數化查詢，防止 SQL 注入)
            search_pattern = f"%{keyword}%"

            # ==================== 步驟 1: 統計匹配訊息數 ====================

            message_match_subquery = (
                select(
                    ChatMessage.session_id,
                    func.count(ChatMessage.id).label('match_count')
                )
                .join(ChatSession, ChatMessage.session_id == ChatSession.id)
                .where(
                    and_(
                        ChatMessage.content.ilike(search_pattern),
                        ChatSession.user_id == user_id  # 只統計當前使用者的訊息
                    )
                )
                .group_by(ChatMessage.session_id)
                .subquery()
            )

            # ==================== 步驟 2: 主查詢 ====================

            main_query = (
                select(
                    ChatSession,
                    func.coalesce(message_match_subquery.c.match_count, 0).label('match_count')
                )
                .outerjoin(
                    message_match_subquery,
                    ChatSession.id == message_match_subquery.c.session_id
                )
                .where(
                    and_(
                        ChatSession.user_id == user_id,
                        ChatSession.is_active == True,
                        (
                            # 標題匹配
                            ChatSession.title.ilike(search_pattern)
                            # 或訊息內容匹配
                            | (message_match_subquery.c.session_id.isnot(None))
                        )
                    )
                )
                .order_by(
                    desc('match_count'),
                    desc(ChatSession.updated_at)
                )
            )

            # 計算總數
            count_query = select(func.count()).select_from(main_query.subquery())
            total = await self.db.scalar(count_query)

            if not total:
                logger.debug("搜尋無結果", extra={"user_id": user_id, "keyword": keyword})
                return paginated_response(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    message="搜尋完成"
                )

            # 分頁查詢
            offset = (page - 1) * page_size
            result = await self.db.execute(
                main_query.limit(page_size).offset(offset)
            )
            rows = result.all()

            # ==================== 步驟 3: 獲取匹配片段 ====================

            session_ids = [row[0].id for row in rows]
            snippets_dict = {}

            if session_ids:
                # 為每個 session 獲取最多 2 條匹配的訊息
                snippets_query = (
                    select(
                        ChatMessage.session_id,
                        ChatMessage.content,
                        ChatMessage.created_at
                    )
                    .where(
                        and_(
                            ChatMessage.session_id.in_(session_ids),
                            ChatMessage.content.ilike(search_pattern)
                        )
                    )
                    .order_by(ChatMessage.created_at.desc())
                )

                snippets_result = await self.db.execute(snippets_query)

                # 組織片段 (每個 session 最多 2 條)
                for row in snippets_result:
                    session_id = row[0]
                    content = row[1]

                    if session_id not in snippets_dict:
                        snippets_dict[session_id] = []

                    if len(snippets_dict[session_id]) < 2:
                        snippet = self._extract_snippet(content, keyword, max_length=100)
                        snippets_dict[session_id].append(snippet)

            # ==================== 步驟 4: 組裝結果 ====================

            items = []
            for row in rows:
                session = row[0]
                match_count = row[1]

                # 使用字典展開,避免 ORM 序列化問題
                session_dict = {
                    "id": session.id,
                    "user_id": session.user_id,
                    "title": session.title,
                    "graph_type": session.graph_type,
                    "collection_ids": session.collection_ids,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active,
                    "match_count": match_count,
                    "matched_snippets": snippets_dict.get(session.id, []),
                    "highlight_keyword": keyword
                }

                items.append(SessionResponse(**session_dict))

            duration = int((time.time() - start_time) * 1000)
            logger.debug(
                f"搜尋完成: 找到 {total} 個結果",
                extra={
                    "user_id": user_id,
                    "keyword": keyword,
                    "total": total,
                    "duration_ms": duration
                }
            )

            return paginated_response(
                items=items,
                total=total or 0,
                page=page,
                page_size=page_size,
                message="搜尋完成"
            )

        except SQLAlchemyError as e:
            logger.error(
                "搜尋對話失敗 - 資料庫錯誤",
                extra={
                    "user_id": user_id,
                    "keyword": keyword,
                    "error": str(e)
                },
                exc_info=True
            )
            raise DatabaseError("搜尋失敗,請稍後再試")

        except Exception as e:
            logger.error(
                "搜尋對話失敗 - 未知錯誤",
                extra={
                    "user_id": user_id,
                    "keyword": keyword,
                    "error": str(e)
                },
                exc_info=True
            )
            raise AppException("搜尋失敗,請聯繫管理員")

    def _extract_snippet(
        self,
        content: str,
        keyword: str,
        max_length: int = 100
    ) -> str:
        """
        提取包含關鍵字的片段

        Args:
            content: 原始內容
            keyword: 搜尋關鍵字
            max_length: 片段最大長度

        Returns:
            包含關鍵字的片段
        """
        keyword_lower = keyword.lower()
        content_lower = content.lower()

        idx = content_lower.find(keyword_lower)
        if idx == -1:
            # 找不到關鍵字,返回開頭
            return content[:max_length] + ("..." if len(content) > max_length else "")

        # 以關鍵字為中心,向前後各取一半
        half_length = max_length // 2
        start = max(0, idx - half_length)
        end = min(len(content), idx + len(keyword) + half_length)

        snippet = content[start:end]

        # 添加省略號
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    # ==================== 訊息管理 ====================

    async def get_messages(
        self,
        session_id: UUID,
        user_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> ApiResponse[PaginatedResponse[MessageResponse]]:
        """取得 Session 的歷史訊息（分頁）"""
        # 驗證權限
        await self._get_session_or_404(session_id, user_id)

        # 查詢
        query = select(ChatMessage).where(ChatMessage.session_id == session_id)

        # 計算總數
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # 分頁查詢（升序，最舊的在前）
        query = query.order_by(ChatMessage.created_at)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        messages = result.scalars().all()

        # 查詢使用者對助手訊息的反饋
        assistant_message_ids = [m.id for m in messages if m.role == "assistant"]
        feedbacks_dict = {}

        if assistant_message_ids:
            feedback_query = select(MessageFeedback).where(
                and_(
                    MessageFeedback.message_id.in_(assistant_message_ids),
                    MessageFeedback.user_id == user_id
                )
            )
            feedback_result = await self.db.execute(feedback_query)
            feedbacks = feedback_result.scalars().all()
            feedbacks_dict = {fb.message_id: fb for fb in feedbacks}

        # 組裝回應,為助手訊息附加反饋
        items = []
        for m in messages:
            message_data = MessageResponse.from_orm(m)
            if m.role == "assistant" and m.id in feedbacks_dict:
                # 將 FeedbackResponse 轉為字典,避免跨模組 Schema 依賴
                feedback_obj = FeedbackResponse.model_validate(feedbacks_dict[m.id])
                message_data.user_feedback = feedback_obj.model_dump()
            items.append(message_data)

        return paginated_response(
            items=items,
            total=total or 0,
            page=page,
            page_size=page_size,
            message="訊息獲取成功"
        )

    async def stream_chat(
        self,
        session_id: UUID,
        user_id: int,
        content: str,
        attachments: List[Dict[str, Any]] = None,
        prompt_template_id: Optional[UUID] = None
    ) -> AsyncGenerator[MessageChunk, None]:
        """發送訊息（串流,支援附件,支援自訂提示詞）"""
        start_time = time.time()

        # 記錄開始處理
        logger.debug(
            f"開始處理聊天請求: stream_chat (session={session_id}, content_length={len(content)}, "
            f"attachments={len(attachments) if attachments else 0}, "
            f"prompt_template_id={prompt_template_id})"
        )

        try:
            # 驗證權限並取得 Session
            session = await self._get_session_or_404(session_id, user_id)

            logger.debug(f"Session 驗證通過: {session.graph_type}")

            # 載入自訂提示詞（如果提供）
            custom_prompt = None
            prompt_name = None
            if prompt_template_id:
                from app.db.models.prompt_template import PromptTemplate
                stmt = select(PromptTemplate).where(
                    and_(
                        PromptTemplate.id == prompt_template_id,
                        PromptTemplate.user_id == user_id,
                        PromptTemplate.is_active == True
                    )
                )
                result = await self.db.execute(stmt)
                template = result.scalar_one_or_none()

                if template:
                    custom_prompt = template.content
                    prompt_name = template.name
                    logger.info(
                        f"使用自訂提示詞",
                        extra={
                            "template_id": str(prompt_template_id),
                            "template_name": prompt_name,
                            "session_id": str(session_id)
                        }
                    )
                else:
                    logger.warning(
                        f"提示詞模板不存在或無權限",
                        extra={
                            "template_id": str(prompt_template_id),
                            "user_id": user_id
                        }
                    )

            # 先取得歷史訊息（在儲存新訊息之前，避免快取誤判）
            logger.debug("正在讀取歷史訊息...")
            history = await self._get_history_for_graph(session_id)
            logger.debug(f"歷史訊息讀取完成: {len(history)} 條")

            # 再儲存使用者訊息（包含附件）
            logger.debug("正在儲存使用者訊息...")
            user_message = await self._save_message(
                session_id=session_id,
                role="user",
                content=content,
                attachments=attachments  # 新增參數
            )
            logger.debug(f"使用者訊息已儲存: {user_message.id}, 附件數: {len(attachments) if attachments else 0}")

            # 立即發送使用者訊息（包含附件資訊）給前端
            from app.modules.chat.schemas import MessageResponse, MessageChunk
            user_message_response = MessageResponse.from_orm(user_message)
            yield MessageChunk(
                type="user_message",
                message=user_message_response
            )

            # 準備傳遞給 Graph 的附件資料
            graph_attachments = None
            if attachments:
                # 使用 AttachmentConverter 服務
                graph_attachments = await self.attachment_converter.convert_to_graph_format(attachments)

            # 對 agent_graph：查詢 session 歷史檔案附件，確保跨輪對話可用
            if session.graph_type == "agent_graph":
                history_file_attachments = await self._get_session_file_attachments(session_id)
                if history_file_attachments:
                    if graph_attachments is None:
                        graph_attachments = []
                    current_paths = {a["file_path"] for a in graph_attachments if a.get("type") == "file"}
                    max_files = self.settings.CHAT_MAX_FILES_PER_MESSAGE
                    for att in history_file_attachments:
                        if len(graph_attachments) >= max_files:
                            break
                        if att["file_path"] not in current_paths:
                            graph_attachments.append({
                                "id": str(att["id"]),
                                "type": "file",
                                "file_path": att["file_path"],
                                "original_filename": att["original_filename"],
                                "metadata": {
                                    "file_size": att["file_size"],
                                    "mime_type": att["mime_type"],
                                }
                            })

            # 執行 Graph（串流）
            executor = GraphExecutor(session.graph_type, self.settings)

            assistant_content = ""
            metadata = {}

            async for event in executor.stream_execute(
                user_query=content,
                history_messages=history,
                collection_ids=session.collection_ids,
                attachments=graph_attachments,
                custom_system_prompt=custom_prompt  # 新增參數：自訂提示詞
            ):
                if event["type"] == "token":
                    # 逐字累積助手回應
                    assistant_content += event["content"]
                    yield MessageChunk(type="token", content=event["content"])

                elif event["type"] == "metadata":
                    # 中間節點資訊
                    metadata_step = event.get("step", "")
                    metadata_data = event.get("data", {})
                    # 扁平化 metadata：直接合併到根層級，而非按 step 分組
                    metadata.update(metadata_data)
                    yield MessageChunk(
                        type="metadata",
                        step=metadata_step,
                        data=metadata_data
                    )

                elif event["type"] == "node_start":
                    yield MessageChunk(type="node_start", node=event.get("node"))

                elif event["type"] == "node_end":
                    yield MessageChunk(type="node_end", node=event.get("node"))

                elif event["type"] == "tool_call":
                    tool_call_data = event.get("data", {})
                    metadata.setdefault("tool_calls", []).append(tool_call_data)
                    yield MessageChunk(type="tool_call", data=tool_call_data)

                elif event["type"] == "tool_result":
                    tool_result_data = event.get("data", {})
                    metadata.setdefault("tool_results", []).append(tool_result_data)
                    yield MessageChunk(type="tool_result", data=tool_result_data)

                elif event["type"] == "error":
                    # executor 回報錯誤，直接轉發給前端並中止
                    yield MessageChunk(type="error", content=event.get("content", "AI 服務發生未知錯誤"))
                    return

                elif event["type"] == "done":
                    break

            # 儲存助手回應
            metadata["processing_time"] = time.time() - start_time

            # 記錄使用的提示詞資訊
            if prompt_template_id:
                metadata["prompt_template_id"] = str(prompt_template_id)
                metadata["prompt_template_name"] = prompt_name

            assistant_message = await self._save_message(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
                extra_data=metadata
            )

            # 更新 Session 的 updated_at
            session.updated_at = datetime.utcnow()
            await self.db.commit()

            # 發送完成訊號，包含 message_id 和完整 metadata
            yield MessageChunk(
                type="done",
                data={
                    "message_id": str(assistant_message.id),
                    **metadata
                }
            )

        except Exception as e:
            # 發送錯誤
            yield MessageChunk(type="error", content=str(e))

    async def save_partial_message(
        self,
        session_id: UUID,
        user_id: int,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> ApiResponse[MessageResponse]:
        """
        保存部分訊息（用於中斷情境）
        
        當使用者中斷 LLM 回覆時，將已經輸出的部分內容保存到資料庫，
        以便使用者可以對中斷的訊息進行反饋。
        
        註：包含防重複保存機制，如果 stream_chat 已經保存完整訊息，
        則直接返回已存在的訊息，避免競態條件導致的重複保存。
        """
        # 驗證權限並取得 Session
        session = await self._get_session_or_404(session_id, user_id)
        
        # 如果沒有內容，不保存
        if not content or not content.strip():
            raise ValidationError("訊息內容不能為空")
        
        # 🔍 防重複保存：檢查是否已經有完整訊息（競態條件）
        # 查詢這個 session 的最後一條 assistant 訊息
        last_message_query = select(ChatMessage).where(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "assistant"
            )
        ).order_by(desc(ChatMessage.created_at)).limit(1)
        
        result = await self.db.execute(last_message_query)
        last_message = result.scalar_one_or_none()
        
        # 如果已經有訊息且不是中斷訊息，檢查是否是競態條件
        if last_message and not last_message.extra_data.get("interrupted"):
            # 計算時間差（秒）- 使用 aware datetime 進行比較
            now_utc = datetime.now(timezone.utc)
            time_diff = (now_utc - last_message.created_at).total_seconds()
            
            # 只有在 5 秒內創建的完整訊息才認為是競態條件
            # （正常的競態窗口 < 1 秒，5 秒是安全邊界）
            if time_diff < 5:
                logger.info(
                    f"檢測到競態條件：完整訊息已存在，跳過部分訊息保存 "
                    f"(session={session_id}, message={last_message.id}, time_diff={time_diff:.2f}s)"
                )
                # 直接返回已存在的完整訊息
                return success_response(
                    data=MessageResponse.from_orm(last_message),
                    message="訊息已完成"
                )
        
        # 準備 metadata，標記為中斷訊息
        extra_data = metadata or {}
        extra_data["interrupted"] = True
        extra_data["interrupted_at"] = datetime.utcnow().isoformat()
        
        # 儲存助手回應（部分內容）
        assistant_message = await self._save_message(
            session_id=session_id,
            role="assistant",
            content=content,
            extra_data=extra_data
        )
        
        # 更新 Session 的 updated_at
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        
        logger.info(
            f"部分訊息已保存 (session={session_id}, message={assistant_message.id}, content_length={len(content)})"
        )
        
        # 返回完整訊息
        return success_response(
            data=MessageResponse.from_orm(assistant_message),
            message="部分訊息已保存"
        )

    async def get_attachment(
        self,
        message_id: UUID,
        attachment_id: UUID,
        user_id: int
    ) -> MessageAttachment:
        """
        取得訊息附件

        驗證使用者權限後返回附件資訊。
        """
        # 先驗證訊息權限
        query = select(ChatMessage).join(ChatSession).where(
            and_(
                ChatMessage.id == message_id,
                ChatSession.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            raise ResourceNotFoundError("訊息不存在或無權限訪問")

        # 查詢附件
        query = select(MessageAttachment).where(
            and_(
                MessageAttachment.id == attachment_id,
                MessageAttachment.message_id == message_id
            )
        )
        result = await self.db.execute(query)
        attachment = result.scalar_one_or_none()

        if not attachment:
            raise ResourceNotFoundError("附件不存在")

        return attachment

    # ==================== 輔助方法 ====================

    async def _get_session_or_404(
        self,
        session_id: UUID,
        user_id: int
    ) -> ChatSession:
        """取得 Session 或拋出異常"""
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise ResourceNotFoundError("Session", str(session_id))

        return session

    async def _get_session_file_attachments(self, session_id: UUID) -> List[Dict]:
        """查詢 session 中所有 file 類型的歷史附件"""
        from pathlib import Path

        result = await self.db.execute(
            select(MessageAttachment)
            .join(ChatMessage, MessageAttachment.message_id == ChatMessage.id)
            .where(
                ChatMessage.session_id == session_id,
                MessageAttachment.attachment_type == "file"
            )
            .order_by(MessageAttachment.created_at)
        )
        attachments = result.scalars().all()

        valid = []
        for att in attachments:
            if Path(att.file_path).exists():
                valid.append({
                    "id": att.id,
                    "file_path": att.file_path,
                    "original_filename": att.original_filename,
                    "file_size": att.file_size,
                    "mime_type": att.mime_type,
                })
        return valid

    async def _save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        extra_data: dict = None,
        attachments: List[Dict[str, Any]] = None
    ) -> ChatMessage:
        """儲存訊息到資料庫和快取"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            extra_data=extra_data or {}
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # 儲存附件（如果有）
        if attachments:
            for attachment_info in attachments:
                attachment = MessageAttachment(
                    message_id=message.id,
                    attachment_type=attachment_info["type"],
                    file_path=attachment_info["file_path"],
                    original_filename=attachment_info["original_filename"],
                    file_size=attachment_info["file_size"],
                    mime_type=attachment_info["mime_type"],
                    extra_data=attachment_info.get("extra_data", {}),
                    processing_status="completed"
                )
                self.db.add(attachment)

            await self.db.commit()
            await self.db.refresh(message)

            logger.debug(f"訊息附件已儲存: message_id={message.id}, 附件數={len(attachments)}")

        # 嘗試寫入快取（失敗不影響業務流程）
        try:
            await self.cache.save_message(
                session_id=str(session_id),
                message={
                    "role": role,
                    "content": content,
                    "created_at": message.created_at.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"快取訊息失敗（已忽略）: {e}")

        return message

    async def _get_history_for_graph(
        self,
        session_id: UUID
    ) -> List[dict]:
        """
        取得用於 Graph 的歷史訊息
        優先從快取讀取，失敗降級到資料庫
        """
        # 嘗試從快取讀取
        try:
            messages = await self.cache.get_recent_messages(str(session_id))
            if messages:
                logger.debug(f"快取命中: {len(messages)} 條")
                return messages
        except Exception as e:
            logger.warning(
                f"快取讀取失敗，降級到資料庫: {e}",
                extra={"session_id": str(session_id), "error": str(e)}
            )

        # 快取 Miss 或失敗 → 從資料庫讀取
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at)

        result = await self.db.execute(query)
        db_messages = result.scalars().all()

        # 轉換格式
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in db_messages
        ]

        # 重建快取（先清空，避免重複）
        if messages:
            try:
                # 刪除舊快取
                await self.cache.delete_session(str(session_id))
                
                # 寫入新資料
                for msg in messages:
                    await self.cache.save_message(str(session_id), msg)
                
                logger.debug(f"快取已重建: {len(messages)} 條")
            except Exception as e:
                logger.warning(
                    f"快取重建失敗（已忽略）: {e}",
                    extra={"session_id": str(session_id), "error": str(e)}
                )

        return messages
