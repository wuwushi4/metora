/**
 * 法規統計資訊
 */
export interface LawStatistics {
  /** 章數 */
  chapters: number
  /** 條數 */
  articles: number
  /** 項數 */
  items: number
  /** 款數 */
  subitems: number
}

/**
 * 法規處理請求
 */
export interface LawProcessRequest {
  /** 法規編號（1個大寫英文字母 + 7個數字） */
  pcode: string
  /** 法規名稱（可選，如未提供則從網頁提取） */
  law_name?: string
  /** 強制重新爬取（忽略快取） */
  force_refresh?: boolean
}

/**
 * 法規處理回應
 */
export interface LawProcessResponse {
  /** 法規編號 */
  pcode: string
  /** 法規名稱 */
  law_name: string
  /** Markdown 內容 */
  md_content: string
  /** JSON 內容 */
  json_content: Record<string, any>
  /** 建議的 Markdown 檔名 */
  md_filename: string
  /** 建議的 JSON 檔名 */
  json_filename: string
  /** 統計資訊 */
  statistics: LawStatistics
  /** 是否來自快取 */
  from_cache: boolean
  /** 處理耗時（秒） */
  processing_time?: number
}

/**
 * 處理狀態
 */
export type ProcessingStatus = 'idle' | 'processing' | 'success' | 'error'

/**
 * 處理狀態資訊
 */
export interface ProcessingState {
  /** 當前狀態 */
  status: ProcessingStatus
  /** 錯誤訊息 */
  error?: string
  /** 處理結果 */
  result?: LawProcessResponse
}
