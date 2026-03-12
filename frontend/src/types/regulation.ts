/**
 * Regulation 法規管理相關類型定義
 */

/**
 * 所有者資訊
 */
export interface OwnerInfo {
  /** 使用者 ID */
  id: number
  /** 使用者名稱 */
  username: string
  /** 真實姓名 */
  full_name: string | null
}

/**
 * 法規基本資訊
 */
export interface Regulation {
  /** 法規 ID */
  id: number
  /** 法規代碼（如：M0060027） */
  law_code: string
  /** 法規名稱 */
  law_name: string
  /** 法規類別 */
  category: string
  /** 法規狀態（現行/廢止等） */
  status: string
  /** 最後更新日期（YYYY-MM-DD） */
  last_updated: string | null
  /** 所有者 ID */
  user_id: number
  /** 章節總數（後端計算） */
  total_chapters: number
  /** 條文總數（後端計算） */
  total_articles: number
  /** 情境總數（後端計算） */
  total_scenarios: number
  /** 所有者資訊（可選） */
  owner?: OwnerInfo | null
  /** 建立時間 */
  created_at: string
  /** 更新時間 */
  updated_at: string
}

/**
 * 法規列表查詢參數
 */
export interface RegulationListParams {
  /** 頁碼（從 1 開始） */
  page?: number
  /** 每頁筆數 */
  page_size?: number
  /** 法規名稱（模糊搜尋） */
  law_name?: string
  /** 法規類別（精確搜尋） */
  category?: string
  /** 法規狀態（精確搜尋） */
  status?: string
}

/**
 * 法規詳情（包含完整內容）
 */
export interface RegulationDetail extends Regulation {
  /** 完整法規內容 */
  content: RegulationContent
}

/**
 * 法規內容結構
 */
export interface RegulationContent {
  /** 法規基本資料 */
  law_metadata: LawMetadata
  /** 章節列表 */
  chapters: Chapter[]
}

/**
 * 法規基本資料
 */
export interface LawMetadata {
  /** 法規名稱 */
  name: string
  /** 法規類別 */
  category: string
  /** 法規狀態 */
  status: string
  /** 最後更新日期 */
  last_updated: string
  /** 法規代碼 */
  code: string
  /** 法規來源網址 */
  source_url: string
}

/**
 * 章節結構
 */
export interface Chapter {
  /** 章節編號（如：1、4-1） */
  chapter_num: string
  /** 章節顯示名稱（如：第 一 章） */
  chapter_display: string
  /** 章節名稱（如：總則） */
  chapter_name: string
  /** 該章節下的條文列表 */
  articles: Article[]
}

/**
 * 條文結構
 */
export interface Article {
  /** 條文編號（如：1、14-2） */
  article_num: string
  /** 條文顯示名稱（如：第 1 條） */
  article_display: string
  /** 條文內容 */
  content: string
  /** 應用情境列表 */
  scenarios: string[]
}

/**
 * 法規上傳請求
 */
export interface RegulationUploadRequest {
  /** 完整法規內容 */
  content: RegulationContent
}

/**
 * 法規更新請求
 */
export interface RegulationUpdateRequest {
  /** 完整法規內容（包含更新後的 scenarios） */
  content: RegulationContent
}
