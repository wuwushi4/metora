/**
 * Chat 模組型別定義
 */

import type { Feedback } from './feedback'
import type { MessageAttachment } from './upload'

/**
 * Chat Session
 */
export interface ChatSession {
  id: string
  user_id: number
  title: string
  /**
   * Agent 類型
   * - base_graph: 通用助理
   * - rag_graph: 知識專家
   * - regulation_graph: 法規顧問
   * - agent_graph: 工具 Agent
   */
  graph_type: 'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph'
  collection_ids: number[]
  created_at: string
  updated_at: string
  is_active: boolean
  message_count?: number

  // 搜尋相關欄位（僅在搜尋 API 返回時存在）
  match_count?: number
  matched_snippets?: string[]
  highlight_keyword?: string
}

/**
 * Chat Message
 */
export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata: MessageMetadata
  created_at: string
  user_feedback?: Feedback // 使用者對此訊息的反饋（僅 assistant 訊息）
  attachments?: MessageAttachment[] // 訊息附件（僅 user 訊息）
}

/**
 * 訊息元資料
 */
export interface MessageMetadata {
  // RAG 檢索結果
  retrieval_results?: RetrievalResult[]
  // 查詢重構產生的子問題
  sub_queries?: SubQuery[]
  // 意圖判別結果
  need_rag?: boolean
  // 意圖判別理由
  intent_reason?: string
  // 處理時間（秒）
  processing_time?: number
  // 提示詞模板 ID（如有使用）
  prompt_template_id?: string
  // 提示詞模板名稱（如有使用）
  prompt_template_name?: string
  // Agent 工具呼叫記錄
  tool_calls?: ToolCallRecord[]
  // Agent 工具執行結果
  tool_results?: ToolResultRecord[]
  // 其他自訂資料
  [key: string]: any
}

export interface ToolOutputFile {
  filename: string
  content_base64: string
  mime_type: string
  size: number
}

export interface ToolCallRecord {
  tool_name: string
  tool_call_id?: string
  code?: string
}

export interface ToolResultRecord {
  tool_name: string
  content: string
  output_files?: ToolOutputFile[]
}

/**
 * 檢索結果
 */
export interface RetrievalResult {
  filename: string
  content: string
  score: number
  collection_name?: string
  metadata?: Record<string, any>
}

/**
 * 子問題
 */
export interface SubQuery {
  original: string
  rewritten: string
}

/**
 * 訊息 Chunk (SSE 串流)
 * 使用 Discriminated Union 模式確保類型安全
 */
export type MessageChunk
  = | UserMessageChunk
    | NodeStartChunk
    | NodeEndChunk
    | MetadataChunk
    | TokenChunk
    | ToolCallChunk
    | ToolResultChunk
    | DoneChunk
    | ErrorChunk

/**
 * 使用者訊息事件（包含附件）
 */
export interface UserMessageChunk {
  type: 'user_message'
  message: ChatMessage
}

/**
 * 節點開始事件
 */
export interface NodeStartChunk {
  type: 'node_start'
  node: string
}

/**
 * 節點結束事件
 */
export interface NodeEndChunk {
  type: 'node_end'
  node: string
}

/**
 * 元資料事件（根據 step 細分）
 */
export type MetadataChunk
  = | IntentCheckMetadata
    | QueryRewriteMetadata
    | RagRetrievalMetadata

export interface IntentCheckMetadata {
  type: 'metadata'
  step: 'intent_check'
  data: {
    need_rag: boolean
    intent_reason: string
  }
}

export interface QueryRewriteMetadata {
  type: 'metadata'
  step: 'query_rewrite'
  data: {
    sub_queries: SubQuery[]
  }
}

export interface RagRetrievalMetadata {
  type: 'metadata'
  step: 'rag_retrieval'
  data: {
    results_count: number
    retrieval_results: RetrievalResult[]
  }
}

/**
 * 工具呼叫事件（Agent Graph）
 */
export interface ToolCallChunk {
  type: 'tool_call'
  data: {
    tool_name: string
    tool_call_id?: string
    args?: Record<string, any>
  }
}

/**
 * 工具結果事件（Agent Graph）
 */
export interface ToolResultChunk {
  type: 'tool_result'
  data: {
    tool_name: string
    content: string
    output_files?: ToolOutputFile[]
  }
}

/**
 * Token 串流事件
 */
export interface TokenChunk {
  type: 'token'
  content: string
}

/**
 * 完成事件
 */
export interface DoneChunk {
  type: 'done'
  data: {
    message_id: string
    processing_time?: number
  }
}

/**
 * 錯誤事件
 */
export interface ErrorChunk {
  type: 'error'
  content: string
}

/**
 * Chunk 元資料 (用於前端狀態管理)
 */
export interface ChunkMetadata {
  message_id?: string
  node_name?: string
  step?: string
  retrieval_results?: RetrievalResult[]
  sub_queries?: SubQuery[]
  need_rag?: boolean
  intent_reason?: string
  results_count?: number
  processing_time?: number
  tool_calls?: ToolCallRecord[]
  tool_results?: ToolResultRecord[]
  [key: string]: any
}

/**
 * Agent 資訊 (Graph 資訊)
 */
export interface GraphInfo {
  /**
   * Agent 類型
   * - base_graph: 通用助理
   * - rag_graph: 知識專家
   * - regulation_graph: 法規顧問
   * - agent_graph: 工具 Agent
   */
  graph_type: 'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph'
  /** Agent 名稱 */
  name: string
  /** Agent 描述 */
  description: string
  /** 是否需要選擇知識庫 */
  supports_collections: boolean
}

/**
 * Session 建立請求
 */
export interface SessionCreateRequest {
  /** 對話標題 (可選) */
  title?: string
  /**
   * 選擇的 Agent 類型
   * - base_graph: 通用助理
   * - rag_graph: 知識專家
   * - regulation_graph: 法規顧問
   * - agent_graph: 工具 Agent
   */
  graph_type: 'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph'
  /** 知識庫 ID 列表 (知識專家和法規顧問必填) */
  collection_ids: number[]
}

/**
 * Session 更新請求
 */
export interface SessionUpdateRequest {
  title?: string
}

/**
 * 訊息發送請求（multipart/form-data）
 * 注意: 實際發送時使用 FormData
 */
export interface MessageSendRequest {
  content: string
  files?: File[]
  /** 提示詞模板 ID（選填） */
  prompt_template_id?: string
}

/**
 * Graph 列表響應
 */
export type GraphListResponse = GraphInfo[]

/**
 * 類型守衛：判斷 Session 是否為搜尋結果
 *
 * 用於在運行時檢查 Session 物件是否包含搜尋相關欄位
 *
 * @param session - 要檢查的 Session 物件
 * @returns 如果是搜尋結果則返回 true
 *
 * @example
 * ```typescript
 * if (isSessionSearchResult(session)) {
 *   // TypeScript 會自動推斷 session 包含 match_count 等欄位
 *   console.log(session.match_count)
 * }
 * ```
 */
export function isSessionSearchResult(
  session: ChatSession,
): session is ChatSession & Required<Pick<ChatSession, 'match_count' | 'matched_snippets'>> {
  return (
    typeof session.match_count === 'number'
    && Array.isArray(session.matched_snippets)
  )
}
