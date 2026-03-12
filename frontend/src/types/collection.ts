/**
 * Collection 基本資訊
 */
export interface Collection {
  /** Collection ID */
  id: number
  /** Collection 名稱 */
  name: string
  /** Collection 描述 */
  description: string | null
  /** 所有者 ID */
  user_id: number
  /** 分塊策略 */
  chunking_strategy: string
  /** 關聯的 Dataset 數量 */
  dataset_count: number
  /** 建立時間 */
  created_at: string
  /** 更新時間 */
  updated_at: string
  /** 所有者資訊（可選，由後端提供） */
  owner?: {
    id: number
    username: string
    full_name: string | null
  }
}

/**
 * 建立 Collection 請求
 */
export interface CollectionCreateRequest {
  /** Collection 名稱 */
  name: string
  /** Collection 描述（可選） */
  description?: string
  /** 分塊策略 */
  chunking_strategy: string
}

/**
 * 更新 Collection 請求
 */
export interface CollectionUpdateRequest {
  /** Collection 名稱（可選） */
  name?: string
  /** Collection 描述（可選） */
  description?: string
}

/**
 * Collection 列表查詢參數
 */
export interface CollectionListParams {
  /** 頁碼 */
  page?: number
  /** 每頁筆數 */
  page_size?: number
  /** 名稱模糊搜尋 */
  name?: string
  /** 分塊策略篩選 */
  chunking_strategy?: string
}
