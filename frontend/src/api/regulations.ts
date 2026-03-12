import type { ApiResponse, PaginationResponse } from '@/types/api'
import type {
  Regulation,
  RegulationDetail,
  RegulationListParams,
  RegulationUpdateRequest,
  RegulationUploadRequest,
} from '@/types/regulation'
import { del, get, post, put } from './request'

/**
 * 獲取法規列表 API
 *
 * @param params - 查詢參數(分頁、篩選)
 * @returns 法規列表響應(含分頁資訊)
 */
export async function getRegulationList(params: RegulationListParams = {}) {
  const response = await get<ApiResponse<PaginationResponse<Regulation>>>(
    '/v1/regulations',
    { params },
  )

  if (!response.data) {
    throw new Error('獲取法規列表失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 根據 ID 獲取法規詳情 API
 *
 * @param id - 法規 ID
 * @returns 法規詳細資料（包含完整內容）
 */
export async function getRegulationById(id: number): Promise<RegulationDetail> {
  const response = await get<ApiResponse<RegulationDetail>>(`/v1/regulations/${id}`)

  if (!response.data) {
    throw new Error('獲取法規失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 上傳法規 JSON 文件建立新法規 API
 *
 * @param data - 法規上傳請求資料
 * @returns 新建立的法規資料
 */
export async function uploadRegulation(
  data: RegulationUploadRequest,
): Promise<Regulation> {
  const response = await post<ApiResponse<Regulation>>('/v1/regulations', data)

  if (!response.data) {
    throw new Error('上傳法規失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 更新法規 API（主要更新 scenarios）
 *
 * @param id - 法規 ID
 * @param data - 法規更新請求資料
 * @returns 更新後的法規資料
 */
export async function updateRegulation(
  id: number,
  data: RegulationUpdateRequest,
): Promise<Regulation> {
  const response = await put<ApiResponse<Regulation>>(
    `/v1/regulations/${id}`,
    data,
  )

  if (!response.data) {
    throw new Error('更新法規失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 刪除法規 API
 *
 * @param id - 法規 ID
 */
export async function deleteRegulation(id: number): Promise<void> {
  await del<ApiResponse<{ message: string }>>(`/v1/regulations/${id}`)
}

/**
 * 導出法規為 JSON 文件 API
 *
 * @param id - 法規 ID
 * @returns Blob 對象（JSON 文件）
 */
export async function exportRegulation(id: number): Promise<Blob> {
  const response = await get<Blob>(
    `/v1/regulations/${id}/export`,
    { responseType: 'blob' },
  )

  return response
}
