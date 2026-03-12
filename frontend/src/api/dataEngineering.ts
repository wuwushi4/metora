import type { ApiResponse } from '@/types/api'
import type { LawProcessRequest, LawProcessResponse } from '@/types/dataEngineering'
import { post } from './request'

/**
 * 處理法規資料 API
 *
 * @param request - 法規處理請求
 * @returns 處理結果（含 MD 和 JSON 內容）
 */
export async function processLaw(
  request: LawProcessRequest,
): Promise<LawProcessResponse> {
  const response = await post<ApiResponse<LawProcessResponse>>(
    '/v1/data-engineering/laws/process',
    request,
  )

  if (!response.data) {
    throw new Error('處理法規失敗：無效的響應格式')
  }

  return response.data
}
