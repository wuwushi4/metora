import type { ApiResponse, PaginationResponse } from '@/types/api'
import type {
  ChunkingDefaults,
  Dataset,
  DatasetListParams,
  DatasetUploadResponse,
} from '@/types/dataset'
import { del, get, post } from './request'

/**
 * 獲取 Dataset 列表 API
 *
 * @param params - 查詢參數(分頁、篩選)
 * @returns Dataset 列表響應(含分頁資訊)
 */
export async function getDatasetList(params: DatasetListParams = {}) {
  const response = await get<ApiResponse<PaginationResponse<Dataset>>>(
    '/v1/datasets',
    { params },
  )

  if (!response.data) {
    throw new Error('獲取 Dataset 列表失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 根據 ID 獲取 Dataset API
 *
 * @param id - Dataset ID
 * @returns Dataset 資料
 */
export async function getDatasetById(id: number): Promise<Dataset> {
  const response = await get<ApiResponse<Dataset>>(`/v1/datasets/${id}`)

  if (!response.data) {
    throw new Error('獲取 Dataset 失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 取得遞迴分塊預設參數
 *
 * @returns 目前有效的分塊預設值（系統設定 > 環境變數）
 */
export async function getChunkingDefaults(): Promise<ChunkingDefaults> {
  const response = await get<ApiResponse<ChunkingDefaults>>(
    '/v1/datasets/chunking-defaults',
  )

  if (!response.data) {
    throw new Error('取得分塊預設參數失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 上傳檔案並建立 Dataset API
 *
 * @param collectionId - Collection ID
 * @param file - 要上傳的檔案
 * @param options - 可選的分塊參數
 * @returns 上傳結果(含新建立的 Dataset)
 */
export async function uploadDataset(
  collectionId: number,
  file: File,
  options?: { chunkSize?: number, chunkOverlap?: number },
): Promise<DatasetUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const params = new URLSearchParams()
  params.set('collection_id', String(collectionId))
  if (options?.chunkSize != null)
    params.set('chunk_size', String(options.chunkSize))
  if (options?.chunkOverlap != null)
    params.set('chunk_overlap', String(options.chunkOverlap))

  const response = await post<ApiResponse<DatasetUploadResponse>>(
    `/v1/datasets/upload?${params.toString()}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  )

  if (!response.data) {
    throw new Error('上傳 Dataset 失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 刪除 Dataset API
 *
 * @param id - Dataset ID
 */
export async function deleteDataset(id: number): Promise<void> {
  await del<ApiResponse<{ message: string }>>(`/v1/datasets/${id}`)
}
