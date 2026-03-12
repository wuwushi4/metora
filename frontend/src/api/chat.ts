import type { ApiResponse, PaginationParams, PaginationResponse } from '@/types/api'
import type {
  ChatMessage,
  ChatSession,
  GraphInfo,
  SessionCreateRequest,
  SessionUpdateRequest,
} from '@/types/chat'
/**
 * Chat API 封裝
 */
import { del, get, patch, post } from './request'

// ==================== Graph ====================

/**
 * 取得所有可用的 Graph
 */
export async function getGraphs(): Promise<GraphInfo[]> {
  const response = await get<ApiResponse<GraphInfo[]>>('/v1/chat/graphs')
  return response.data || []
}

// ==================== Session ====================

/**
 * 建立新的聊天 Session
 */
export async function createSession(
  data: SessionCreateRequest,
): Promise<ChatSession> {
  const response = await post<ApiResponse<ChatSession>>('/v1/chat/sessions', data)
  return response.data!
}

/**
 * 取得使用者的 Sessions（分頁）
 */
export async function getSessions(
  params: Partial<PaginationParams> & { is_active?: boolean },
): Promise<PaginationResponse<ChatSession>> {
  const response = await get<ApiResponse<PaginationResponse<ChatSession>>>('/v1/chat/sessions', { params })
  return response.data!
}

/**
 * 取得單一 Session 詳情
 */
export async function getSessionById(id: string): Promise<ChatSession> {
  const response = await get<ApiResponse<ChatSession>>(`/v1/chat/sessions/${id}`)
  return response.data!
}

/**
 * 更新 Session
 */
export async function updateSession(
  id: string,
  data: SessionUpdateRequest,
): Promise<ChatSession> {
  const response = await patch<ApiResponse<ChatSession>>(`/v1/chat/sessions/${id}`, data)
  return response.data!
}

/**
 * 刪除 Session（軟刪除）
 */
export async function deleteSession(id: string): Promise<void> {
  await del<ApiResponse<void>>(`/v1/chat/sessions/${id}`)
}

/**
 * 搜尋對話記錄
 *
 * 根據關鍵字搜尋使用者的對話標題和訊息內容
 *
 * @param params - 搜尋參數
 * @param params.keyword - 搜尋關鍵字（至少 2 個字元）
 * @param params.page - 頁碼（預設 1）
 * @param params.page_size - 每頁數量（預設 20）
 * @returns 搜尋結果（包含匹配的訊息片段）
 *
 * @example
 * ```typescript
 * const result = await searchSessions({ keyword: '法規', page: 1, page_size: 20 })
 * console.log(result.items) // 搜尋到的 sessions
 * ```
 */
export async function searchSessions(params: {
  keyword: string
  page?: number
  page_size?: number
}): Promise<PaginationResponse<ChatSession>> {
  const response = await get<ApiResponse<PaginationResponse<ChatSession>>>(
    '/v1/chat/sessions/search',
    { params: { keyword: params.keyword, page: params.page || 1, page_size: params.page_size || 20 } },
  )
  return response.data!
}

// ==================== Message ====================

/**
 * 取得 Session 的歷史訊息（分頁）
 */
export async function getMessages(
  sessionId: string,
  params: Partial<PaginationParams>,
): Promise<PaginationResponse<ChatMessage>> {
  const response = await get<ApiResponse<PaginationResponse<ChatMessage>>>(
    `/v1/chat/sessions/${sessionId}/messages`,
    { params },
  )
  return response.data!
}

/**
 * 注意：訊息發送使用 SSE 串流
 * 請使用 useChatMessage composable 處理
 * 不在 API 層暴露 SSE 相關函數
 */

/**
 * 保存部分訊息（用於中斷情境）
 *
 * 當使用者中斷 LLM 串流輸出時，調用此函數保存已經輸出的部分內容
 */
export async function savePartialMessage(
  sessionId: string,
  content: string,
  metadata?: Record<string, any>,
): Promise<ChatMessage> {
  const response = await post<ApiResponse<ChatMessage>>(
    `/v1/chat/sessions/${sessionId}/messages/partial`,
    {
      content,
      metadata: metadata || {},
    },
  )
  return response.data!
}

// ==================== Attachment ====================

/**
 * 取得附件 URL（用於顯示圖片）
 *
 * @param messageId 訊息 ID
 * @param attachmentId 附件 ID
 * @returns 附件的完整 URL
 */
export function getAttachmentUrl(messageId: string, attachmentId: string): string {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002/api'
  return `${baseURL}/v1/chat/messages/${messageId}/attachments/${attachmentId}`
}
