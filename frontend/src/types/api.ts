/**
 * API 通用響應型別定義
 */

/**
 * 通用 API 響應格式（符合後端 FastAPI 規範）
 * @template T - 響應資料的型別
 */
export interface ApiResponse<T = any> {
  /** 請求是否成功 */
  success: boolean
  /** 響應資料 */
  data?: T
  /** 響應訊息 */
  message?: string
  /** 狀態碼（用於前端識別） */
  code: string
}

/**
 * API 錯誤響應格式（符合後端 FastAPI 規範）
 */
export interface ApiError {
  /** 請求是否成功（錯誤時為 false） */
  success: false
  /** 錯誤訊息 */
  message: string
  /** 錯誤狀態碼（用於前端識別） */
  code: string
  /** 詳細錯誤資訊（可選） */
  details?: any
}

/**
 * 分頁請求參數
 */
export interface PaginationParams {
  /** 當前頁碼 (從 1 開始) */
  page: number
  /** 每頁資料數量 */
  pageSize: number
  /** 排序欄位 (可選) */
  sortBy?: string
  /** 排序方向 (可選) */
  sortOrder?: 'asc' | 'desc'
}

/**
 * 分頁元資訊（符合後端 PaginationMeta schema）
 */
export interface PaginationMeta {
  /** 總資料數 */
  total: number
  /** 當前頁碼 */
  page: number
  /** 每頁資料數量 */
  page_size: number
  /** 總頁數 */
  total_pages: number
}

/**
 * 分頁響應資料（符合後端 PaginatedResponse schema）
 * @template T - 列表項目的型別
 */
export interface PaginationResponse<T> {
  /** 資料列表 */
  items: T[]
  /** 分頁資訊 */
  pagination: PaginationMeta
}

/**
 * 列表查詢參數
 */
export interface ListQueryParams extends Partial<PaginationParams> {
  /** 搜尋關鍵字 (可選) */
  keyword?: string
  /** 篩選條件 (可選) */
  filters?: Record<string, any>
}
