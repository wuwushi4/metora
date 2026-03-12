/**
 * 訊息反饋相關類型定義
 */

import type { MessageAttachment } from './upload'

/**
 * 反饋類型
 */
export type FeedbackType = 'thumbs_up' | 'thumbs_down'

/**
 * 反饋資料結構
 */
export interface Feedback {
  id: string
  message_id: string
  user_id: number
  feedback_type: FeedbackType
  issue_tags?: string[]
  comment?: string
  created_at: string
  updated_at: string
}

/**
 * 建立反饋請求
 */
export interface FeedbackCreateRequest {
  message_id: string
  feedback_type: FeedbackType
  issue_tags?: string[]
  comment?: string
}

/**
 * 問題標籤列表回應
 */
export interface IssueTagsResponse {
  tags: string[]
}

// ==========================================
// 反饋管理相關類型
// ==========================================

/**
 * 使用者基本資訊
 */
export interface UserBasicInfo {
  id: number
  username: string
  full_name?: string
}

/**
 * 專家審查資料結構
 */
export interface ExpertReview {
  id: string
  feedback_id: string
  expert_opinion: string
  suggested_response?: string
  reviewed_by: number
  reviewer?: UserBasicInfo
  created_at: string
  updated_at: string
}

/**
 * 反饋列表項目 (用於列表頁展示)
 */
export interface FeedbackListItem {
  id: string
  message_id: string
  user: UserBasicInfo
  message_preview: string
  feedback_type: FeedbackType
  issue_tags?: string[]
  is_reviewed: boolean
  is_interrupted: boolean
  created_at: string
  // 新增欄位
  graph_type: string
  collection_ids: number[]
  collection_names: string[]
}

/**
 * 反饋詳情 (用於詳情頁展示)
 */
export interface FeedbackDetail extends Feedback {
  user: UserBasicInfo
  message: {
    id: string
    content: string
    role: string
    extra_data: Record<string, any>
    created_at: string
    attachments?: MessageAttachment[]
  }
  user_question?: string
  user_message?: {
    id: string
    content: string
    role: string
    extra_data: Record<string, any>
    created_at: string
    attachments?: MessageAttachment[]
  }
  expert_review?: ExpertReview
  // 新增欄位
  graph_type: string
  collection_ids: number[]
  collection_names: string[]
}

/**
 * 專家審查請求
 */
export interface ExpertReviewRequest {
  expert_opinion: string
  suggested_response?: string
}

/**
 * 反饋列表查詢參數
 */
export interface FeedbackListParams {
  page?: number
  page_size?: number
  feedback_type?: FeedbackType
  is_reviewed?: boolean
  start_date?: string
  end_date?: string
  // 新增篩選參數
  graph_type?: string
  collection_id?: number
}
