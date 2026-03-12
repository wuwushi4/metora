/**
 * 檔案上傳型別定義
 */

/**
 * 附件類型
 */
export type AttachmentType = 'image' | 'pdf_page' | 'file'

/**
 * 上傳檔案狀態
 */
export type UploadStatus = 'pending' | 'uploading' | 'success' | 'error'

/**
 * 前端檔案預覽資訊
 */
export interface FilePreview {
  /** 唯一標識 (前端生成) */
  id: string
  /** 檔案物件 */
  file: File
  /** 預覽 URL (Object URL) */
  previewUrl: string
  /** 檔案類型 */
  type: AttachmentType
  /** 上傳狀態 */
  status: UploadStatus
  /** 錯誤訊息 (如果上傳失敗) */
  error?: string
}

/**
 * 訊息附件 (後端回傳格式)
 */
export interface MessageAttachment {
  /** 附件 ID */
  id: string
  /** 訊息 ID */
  message_id: string
  /** 附件類型 */
  attachment_type: AttachmentType
  /** 檔案儲存路徑 */
  file_path: string
  /** 原始檔案名稱 */
  original_filename: string
  /** 檔案大小 (bytes) */
  file_size: number
  /** MIME 類型 */
  mime_type: string
  /** 附件元資料 (圖片尺寸、PDF 頁碼等) */
  extra_data: Record<string, any>
  /** 處理狀態 */
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  /** 建立時間 */
  created_at: string
}

/**
 * 檔案驗證規則
 */
export interface FileValidationRules {
  /** 最大檔案數量 */
  maxFiles: number
  /** 最大檔案大小 (bytes) */
  maxSize: number
  /** 允許的檔案格式 */
  allowedFormats: string[]
  /** 允許的 MIME 類型 */
  allowedMimeTypes: string[]
}

/**
 * 檔案驗證錯誤類型
 */
export type FileValidationErrorType
  = | 'FILE_TOO_LARGE'
    | 'INVALID_FORMAT'
    | 'TOO_MANY_FILES'
    | 'UNSUPPORTED_TYPE'

/**
 * 檔案驗證錯誤
 */
export interface FileValidationError {
  type: FileValidationErrorType
  message: string
  filename: string
}
