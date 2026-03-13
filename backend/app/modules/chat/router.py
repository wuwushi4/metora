# -*- coding: utf-8 -*-
"""
Chat 模組的 API 路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException, File, Form, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional
from uuid import UUID
from pathlib import Path
from loguru import logger

from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.schemas import UserInfo
from app.modules.chat.service import ChatService
from app.modules.chat.dependencies import get_chat_service
from app.modules.chat.schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    MessageSendRequest,
    MessageResponse,
    MessageChunk,
    GraphInfo,
    PartialMessageCreate,
)
from app.modules.chat.file_processors import (
    ProcessorFactory,
    FileValidationError,
    FileProcessingError,
)
from app.core.config import get_settings, RateLimitLevel
from app.i18n import t
from app.utils.response import ApiResponse, PaginatedResponse
from app.utils.exceptions import AppException
from app.utils.rate_limit import rate_limit


settings = get_settings()

router = APIRouter(prefix="/chat", tags=["Chat"])


# ==================== 輔助函數 ====================

def _handle_sse_error(
    exception: Exception,
    user_id: int,
    session_id: UUID
) -> str:
    """
    統一處理 SSE 串流錯誤

    根據異常類型自動選擇日誌級別和錯誤訊息格式

    Args:
        exception: 拋出的異常
        user_id: 使用者 ID
        session_id: Session ID

    Returns:
        格式化的 SSE error chunk 字串
    """
    if isinstance(exception, AppException):
        # 自定義異常 - 根據 severity 屬性決定日誌級別
        log_level = "WARNING" if exception.severity == "warning" else "ERROR"
        logger.log(
            log_level,
            f"SSE stream failed - {exception.__class__.__name__}: {exception.message}",
            extra={
                "user_id": user_id,
                "session_id": str(session_id),
                "error_code": exception.code,
                "error_details": exception.details
            }
        )
        error_message = exception.message
    else:
        # 未預期的系統異常 - 使用 error 級別
        logger.error(
            f"SSE stream failed - Unexpected error: {str(exception)}",
            extra={
                "user_id": user_id,
                "session_id": str(session_id),
                "error_type": type(exception).__name__
            },
            exc_info=True
        )
        error_message = t('chat.serverError')

    error_chunk = MessageChunk(type="error", content=error_message)
    return f"data: {error_chunk.model_dump_json(exclude_none=True)}\n\n"


# ==================== Graph 資訊 ====================

@router.get("/graphs", response_model=List[GraphInfo])
async def list_graphs():
    """列出所有可用的 Graph"""
    from app.modules.graphs.registry import GraphRegistry
    return GraphRegistry.list_available()


# ==================== Session 管理 ====================

@router.post("/sessions", response_model=ApiResponse[SessionResponse], status_code=201)
async def create_session(
    request: SessionCreateRequest,
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    建立新的聊天 Session

    - **graph_type**: Graph 類型（base_graph 或 rag_graph）
    - **collection_ids**: Collection IDs（僅 rag_graph 需要）
    - **title**: 對話標題（可選）
    """
    return await chat_service.create_session(current_user.id, request)


@router.get("/sessions", response_model=ApiResponse[PaginatedResponse[SessionResponse]])
async def get_sessions(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    is_active: bool = Query(None, description="是否啟用"),
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    取得使用者的 Sessions（分頁）

    返回格式：
    ```json
    {
        "success": true,
        "data": {
            "items": [...],
            "pagination": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    }
    ```
    """
    return await chat_service.get_sessions(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        is_active=is_active
    )


@router.get("/sessions/search", response_model=ApiResponse[PaginatedResponse[SessionResponse]])
@rate_limit(RateLimitLevel.SENSITIVE)
async def search_sessions(
    keyword: str = Query(
        ...,
        min_length=2,
        max_length=50,
        description="搜尋關鍵字 (至少 2 個字元)",
        examples=["法規", "合約範本"]
    ),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    搜尋對話記錄

    根據關鍵字搜尋使用者的對話標題和訊息內容

    - **搜尋範圍**: 對話標題 + 訊息內容
    - **權限控制**: 僅能搜尋自己的對話
    - **速率限制**: 每分鐘 10 次請求
    - **返回結果**: 包含匹配的訊息片段和匹配數量

    **範例**:
    ```
    GET /api/v1/chat/sessions/search?keyword=法規&page=1&page_size=20
    ```

    **返回格式**:
    ```json
    {
        "success": true,
        "data": {
            "items": [
                {
                    "id": "uuid",
                    "title": "法規諮詢",
                    "match_count": 5,
                    "matched_snippets": ["...包含法規的片段..."],
                    ...
                }
            ],
            "pagination": {
                "total": 10,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }
    }
    ```
    """
    return await chat_service.search_sessions(
        user_id=current_user.id,
        keyword=keyword,
        page=page,
        page_size=page_size
    )


@router.get("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def get_session(
    session_id: UUID,
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """取得 Session 詳情"""
    return await chat_service.get_session_by_id(session_id, current_user.id)


@router.patch("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def update_session(
    session_id: UUID,
    request: SessionUpdateRequest,
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """更新 Session（例如：重命名標題）"""
    return await chat_service.update_session(session_id, current_user.id, request)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """刪除 Session"""
    await chat_service.delete_session(session_id, current_user.id)


# ==================== 訊息管理 ====================

@router.get("/sessions/{session_id}/messages", response_model=ApiResponse[PaginatedResponse[MessageResponse]])
async def get_messages(
    session_id: UUID,
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(50, ge=1, le=200, description="每頁數量"),
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    取得 Session 的歷史訊息（分頁）

    返回格式：
    ```json
    {
        "success": true,
        "data": {
            "items": [...],
            "pagination": {
                "total": 50,
                "page": 1,
                "page_size": 50,
                "total_pages": 1
            }
        }
    }
    ```
    """
    return await chat_service.get_messages(
        session_id=session_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    content: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    prompt_template_id: Optional[str] = Form(None, description="提示詞模板 ID"),
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    發送訊息（SSE 串流,支援檔案上傳,支援自訂提示詞）

    支援 multipart/form-data 格式,可同時傳送文字、檔案附件和提示詞 ID。

    **支援的檔案類型**：
    - 圖片: JPG, PNG, GIF, WebP, BMP
    - PDF: 自動轉為圖片序列 (每頁獨立附件,最多 10 頁)

    **自訂提示詞**：
    - `prompt_template_id`: 提示詞模板 ID（可選）
    - 若提供,將使用自訂提示詞替換 Graph 預設提示詞
    - 若不提供,則使用 Graph 內建的預設提示詞

    **事件類型**：
    - `node_start`: 節點開始執行
    - `node_end`: 節點執行完成
    - `metadata`: 中間處理結果（意圖判別、查詢重構、檢索結果）
    - `token`: LLM 回應內容 (逐字串流)
    - `done`: 執行完成
    - `error`: 發生錯誤
    """

    # 1. 驗證 prompt_template_id 格式
    template_uuid = None
    if prompt_template_id:
        try:
            template_uuid = UUID(prompt_template_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=t('chat.promptIdInvalid')
            )

    # 2. 驗證檔案數量
    if files and not settings.CHAT_FILE_UPLOAD_ENABLED:
        raise HTTPException(status_code=400, detail=t('chat.fileFormatDisabled'))

    if files and len(files) > settings.CHAT_MAX_FILES_PER_MESSAGE:
        raise HTTPException(
            status_code=400,
            detail=t('chat.tooManyFiles', max=settings.CHAT_MAX_FILES_PER_MESSAGE)
        )

    # 3. 處理檔案
    processed_attachments = []
    file_errors = []  # 收集檔案處理錯誤
    if files:
        save_dir = Path(settings.CHAT_FILES_STORAGE_PATH)

        for file in files:
            try:
                # 使用工廠模式取得處理器
                processor = ProcessorFactory.get_processor(file.filename, settings)

                # 驗證檔案
                await processor.validate(file)

                # 處理檔案 (返回附件資訊)
                # 注意: PDF 處理器返回列表(多頁),圖片處理器返回單個字典
                attachment_info = await processor.process(file, save_dir)

                # 根據返回類型決定如何添加
                if isinstance(attachment_info, list):
                    # PDF: 多頁附件
                    processed_attachments.extend(attachment_info)
                    logger.info(
                        f"檔案處理成功: {file.filename} (共 {len(attachment_info)} 頁)",
                        extra={
                            "user_id": current_user.id,
                            "session_id": str(session_id),
                            "total_attachments": len(attachment_info),
                        }
                    )
                else:
                    # 圖片: 單一附件
                    processed_attachments.append(attachment_info)
                    logger.info(
                        f"檔案處理成功: {file.filename}",
                        extra={
                            "user_id": current_user.id,
                            "session_id": str(session_id),
                            "attachment_id": attachment_info["id"],
                            "file_size": attachment_info["file_size"],
                        }
                    )

            except FileValidationError as e:
                logger.warning(
                    f"檔案驗證失敗: {e.message}",
                    extra={
                        "user_id": current_user.id,
                        "session_id": str(session_id),
                        "file_name": file.filename,
                        "error_type": "FileValidationError",
                        "error_details": e.details,
                    }
                )
                # 不拋出異常，收集錯誤訊息
                file_errors.append(f"{file.filename}: {e.message}")
            except FileProcessingError as e:
                logger.error(
                    f"檔案處理失敗: {e.message}",
                    extra={
                        "user_id": current_user.id,
                        "session_id": str(session_id),
                        "file_name": file.filename,
                        "error_type": "FileProcessingError",
                        "error_details": e.details,
                    },
                    exc_info=True
                )
                # 不拋出異常，收集錯誤訊息
                file_errors.append(f"{file.filename}: 處理失敗 - {e.message}")
            except Exception as e:
                logger.error(
                    f"檔案處理失敗: 未預期的錯誤",
                    extra={
                        "user_id": current_user.id,
                        "session_id": str(session_id),
                        "file_name": file.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                    exc_info=True
                )
                # 不拋出異常，收集錯誤訊息
                file_errors.append(f"{file.filename}: 處理失敗")

    # 4. SSE 串流
    async def event_generator():
        # 優先檢查檔案錯誤
        if file_errors:
            error_msg = t('chat.fileProcessFailed', errors="\n".join(file_errors))
            error_chunk = MessageChunk(type="error", content=error_msg)
            yield f"data: {error_chunk.model_dump_json(exclude_none=True)}\n\n"
            return

        try:
            async for chunk in chat_service.stream_chat(
                session_id=session_id,
                user_id=current_user.id,
                content=content,
                attachments=processed_attachments,
                prompt_template_id=template_uuid  # 新增參數
            ):
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"

        except Exception as e:
            # 統一處理所有異常 (AppException 和系統異常)
            yield _handle_sse_error(e, current_user.id, session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 緩衝
        }
    )


@router.post("/sessions/{session_id}/messages/partial", response_model=ApiResponse[MessageResponse])
async def save_partial_message(
    session_id: UUID,
    request: PartialMessageCreate,
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    保存部分訊息（用於中斷情境）
    
    當使用者在 LLM 串流輸出過程中點擊停止按鈕時，
    前端會調用此接口保存已經輸出的部分內容，
    以便使用者可以對中斷的訊息進行反饋。
    
    **請求參數**：
    - `content`: 已經輸出的部分內容
    - `metadata`: 元資料（可選，例如已處理的節點資訊）
    
    **返回**：
    - 完整的 MessageResponse，包含真實的 message_id
    
    **特點**：
    - 自動在 metadata 中標記 `interrupted: true`
    - 更新 session 的 updated_at 時間戳
    - 支援使用者對中斷訊息進行反饋
    """
    return await chat_service.save_partial_message(
        session_id=session_id,
        user_id=current_user.id,
        content=request.content,
        metadata=request.metadata
    )


@router.get("/messages/{message_id}/attachments/{attachment_id}")
async def get_attachment(
    message_id: UUID,
    attachment_id: UUID,
    current_user: UserInfo = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    獲取訊息附件檔案

    返回附件的二進制內容,供前端顯示。

    Args:
        message_id: 訊息 ID
        attachment_id: 附件 ID
    """
    # 驗證權限並取得附件
    attachment = await chat_service.get_attachment(
        message_id=message_id,
        attachment_id=attachment_id,
        user_id=current_user.id
    )

    # 檢查檔案是否存在
    file_path = Path(attachment.file_path)
    if not file_path.exists():
        logger.error(
            f"附件檔案不存在: {file_path}",
            extra={
                "user_id": current_user.id,
                "message_id": str(message_id),
                "attachment_id": str(attachment_id),
            }
        )
        raise HTTPException(status_code=404, detail=t('chat.attachmentNotFound'))

    # 返回檔案
    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename
    )
