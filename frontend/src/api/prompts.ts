import type { ApiResponse, PaginationParams, PaginationResponse } from '@/types/api'
import type {
  PromptTemplate,
  PromptTemplateCreateRequest,
  PromptTemplateUpdateRequest,
} from '@/types/prompt'
/**
 * Prompt API 封裝
 */
import { del, get, patch, post } from './request'

// ==================== Prompt Templates ====================

/**
 * 取得使用者的所有提示詞模板（分頁）
 */
export async function getPromptTemplates(
  params?: Partial<PaginationParams> & { is_active?: boolean },
): Promise<PaginationResponse<PromptTemplate>> {
  const response = await get<ApiResponse<PaginationResponse<PromptTemplate>>>(
    '/v1/prompts/templates',
    { params },
  )
  return response.data!
}

/**
 * 建立提示詞模板
 */
export async function createPromptTemplate(
  data: PromptTemplateCreateRequest,
): Promise<PromptTemplate> {
  const response = await post<ApiResponse<PromptTemplate>>(
    '/v1/prompts/templates',
    data,
  )
  return response.data!
}

/**
 * 取得單一提示詞模板
 */
export async function getPromptTemplateById(id: string): Promise<PromptTemplate> {
  const response = await get<ApiResponse<PromptTemplate>>(
    `/v1/prompts/templates/${id}`,
  )
  return response.data!
}

/**
 * 更新提示詞模板
 */
export async function updatePromptTemplate(
  id: string,
  data: PromptTemplateUpdateRequest,
): Promise<PromptTemplate> {
  const response = await patch<ApiResponse<PromptTemplate>>(
    `/v1/prompts/templates/${id}`,
    data,
  )
  return response.data!
}

/**
 * 刪除提示詞模板（軟刪除）
 */
export async function deletePromptTemplate(id: string): Promise<void> {
  await del<ApiResponse<void>>(`/v1/prompts/templates/${id}`)
}

/**
 * 切換收藏狀態
 */
export async function toggleFavorite(id: string): Promise<PromptTemplate> {
  const response = await patch<ApiResponse<PromptTemplate>>(
    `/v1/prompts/templates/${id}/toggle-favorite`,
  )
  return response.data!
}
