/**
 * Dataset 基本資訊
 */
export interface Dataset {
  /** Dataset ID */
  id: number
  /** 所屬 Collection ID */
  collection_id: number
  /** 儲存檔名（UUID） */
  filename: string
  /** 原始檔名 */
  original_filename: string
  /** 檔案路徑 */
  file_path: string
  /** 檔案大小（bytes） */
  file_size: number
  /** 檔案類型 */
  file_type: string
  /** 分塊數量 */
  chunk_count: number
  /** 是否已向量化 */
  vectorized: boolean
  /** 向量化錯誤訊息 */
  vectorization_error: string | null
  /** 建立時間 */
  created_at: string
  /** 更新時間 */
  updated_at: string
}

/**
 * 遞迴分塊預設參數
 */
export interface ChunkingDefaults {
  /** 分塊大小（字元數） */
  chunk_size: number
  /** 重疊大小（字元數） */
  chunk_overlap: number
}

/**
 * Dataset 列表查詢參數
 */
export interface DatasetListParams {
  /** 頁碼 */
  page?: number
  /** 每頁筆數 */
  page_size?: number
  /** 所屬 Collection ID */
  collection_id?: number
  /** 向量化狀態篩選 */
  vectorized?: boolean
  /** 檔名模糊搜尋 */
  original_filename?: string
}

/**
 * 檔案上傳回應
 */
export interface DatasetUploadResponse {
  /** 新建立的 Dataset */
  dataset: Dataset
  /** 訊息 */
  message: string
}
