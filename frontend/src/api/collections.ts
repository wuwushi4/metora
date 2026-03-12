import type { ApiResponse, PaginationResponse } from '@/types/api'
import type {
  Collection,
  CollectionCreateRequest,
  CollectionListParams,
  CollectionUpdateRequest,
} from '@/types/collection'
import { del, get, post, put } from './request'

/**
 * 獲取 Collection 列表 API
 *
 * @param params - 查詢參數(分頁、篩選)
 * @returns Collection 列表響應(含分頁資訊)
 */
export async function getCollectionList(params: CollectionListParams = {}) {
  const response = await get<ApiResponse<PaginationResponse<Collection>>>(
    '/v1/collections',
    { params },
  )

  if (!response.data) {
    throw new Error('獲取 Collection 列表失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 根據 ID 獲取 Collection API
 *
 * @param id - Collection ID
 * @returns Collection 資料
 */
export async function getCollectionById(id: number): Promise<Collection> {
  const response = await get<ApiResponse<Collection>>(`/v1/collections/${id}`)

  if (!response.data) {
    throw new Error('獲取 Collection 失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 建立新 Collection API
 *
 * @param data - Collection 建立請求資料
 * @returns 新建立的 Collection 資料
 */
export async function createCollection(data: CollectionCreateRequest): Promise<Collection> {
  const response = await post<ApiResponse<Collection>>('/v1/collections', data)

  if (!response.data) {
    throw new Error('建立 Collection 失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 更新 Collection API
 *
 * @param id - Collection ID
 * @param data - Collection 更新請求資料
 * @returns 更新後的 Collection 資料
 */
export async function updateCollection(
  id: number,
  data: CollectionUpdateRequest,
): Promise<Collection> {
  const response = await put<ApiResponse<Collection>>(`/v1/collections/${id}`, data)

  if (!response.data) {
    throw new Error('更新 Collection 失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 刪除 Collection API
 *
 * @param id - Collection ID
 */
export async function deleteCollection(id: number): Promise<void> {
  await del<ApiResponse<{ message: string }>>(`/v1/collections/${id}`)
}
