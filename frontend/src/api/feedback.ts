/**
 * 訊息反饋 API
 */

import type { ApiResponse, PaginationResponse } from '@/types/api'
import type {
  ExpertReview,
  ExpertReviewRequest,
  Feedback,
  FeedbackCreateRequest,
  FeedbackDetail,
  FeedbackListItem,
  FeedbackListParams,
  IssueTagsResponse,
} from '@/types/feedback'
import { del, get, post } from './request'

const BASE_PATH = '/v1/feedback'

/**
 * 提交或更新反饋
 */
export function submitFeedback(data: FeedbackCreateRequest): Promise<ApiResponse<Feedback>> {
  return post(BASE_PATH, data)
}

/**
 * 取得訊息的反饋
 */
export function getMessageFeedback(messageId: string): Promise<Feedback | null> {
  return get(`${BASE_PATH}/message/${messageId}`)
}

/**
 * 刪除反饋
 */
export function deleteFeedback(feedbackId: string): Promise<ApiResponse<null>> {
  return del(`${BASE_PATH}/${feedbackId}`)
}

/**
 * 取得問題標籤列表
 */
export function getIssueTags(): Promise<IssueTagsResponse> {
  return get(`${BASE_PATH}/issue-tags`)
}

// ==========================================
// 反饋管理 API (管理員功能)
// ==========================================

/**
 * 獲取反饋列表 API (管理員)
 * @param params - 查詢參數(分頁、篩選)
 * @returns 反饋列表響應(含分頁資訊)
 */
export async function getFeedbackList(params: FeedbackListParams = {}) {
  const response = await get<ApiResponse<PaginationResponse<FeedbackListItem>>>(
    `${BASE_PATH}/management/list`,
    { params },
  )

  if (!response.data) {
    throw new Error('獲取反饋列表失敗:無效的響應格式')
  }

  return response.data
}

/**
 * 獲取反饋詳情 API (管理員)
 * @param feedbackId - 反饋 ID
 * @returns 反饋詳情資料
 */
export async function getFeedbackDetail(feedbackId: string): Promise<FeedbackDetail> {
  const response = await get<ApiResponse<FeedbackDetail>>(
    `${BASE_PATH}/management/${feedbackId}`,
  )

  if (!response.data) {
    throw new Error('獲取反饋詳情失敗:無效的響應格式')
  }

  return response.data
}

/**
 * 提交專家審查 API (管理員)
 * @param feedbackId - 反饋 ID
 * @param data - 審查資料
 * @returns 專家審查資料
 */
export async function submitExpertReview(
  feedbackId: string,
  data: ExpertReviewRequest,
): Promise<ExpertReview> {
  const response = await post<ApiResponse<ExpertReview>>(
    `${BASE_PATH}/management/${feedbackId}/review`,
    data,
  )

  if (!response.data) {
    throw new Error('提交專家審查失敗:無效的響應格式')
  }

  return response.data
}
