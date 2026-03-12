/**
 * Prompt 模組型別定義
 */

/**
 * 提示詞模板
 */
export interface PromptTemplate {
  /** UUID */
  id: string
  /** 使用者 ID */
  user_id: number
  /** 模板名稱 */
  name: string
  /** 提示詞內容 */
  content: string
  /** 描述（選填） */
  description?: string
  /** 是否收藏此提示詞 */
  is_favorite: boolean
  /** 是否啟用 */
  is_active: boolean
  /** 建立時間 */
  created_at: string
  /** 更新時間 */
  updated_at: string
}

/**
 * 建立提示詞模板請求
 */
export interface PromptTemplateCreateRequest {
  /** 模板名稱 (1-100 字) */
  name: string
  /** 提示詞內容 (最多 5000 字) */
  content: string
  /** 描述（選填） */
  description?: string
  /** 是否收藏此提示詞 */
  is_favorite?: boolean
}

/**
 * 更新提示詞模板請求
 */
export interface PromptTemplateUpdateRequest {
  /** 模板名稱 (1-100 字) */
  name?: string
  /** 提示詞內容 (最多 5000 字) */
  content?: string
  /** 描述（選填） */
  description?: string
}
