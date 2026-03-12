/**
 * 聊天錯誤類型定義
 */

/** 錯誤類別 */
export const ChatErrorType = {
  /** 網路連線錯誤 */
  NETWORK_ERROR: 'NETWORK_ERROR',

  /** 認證錯誤 (401, 403) */
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',

  /** 檔案上傳錯誤 (400 - 檔案相關) */
  FILE_UPLOAD_ERROR: 'FILE_UPLOAD_ERROR',

  /** 驗證錯誤 (400 - 非檔案) */
  VALIDATION_ERROR: 'VALIDATION_ERROR',

  /** 伺服器錯誤 (500+) */
  SERVER_ERROR: 'SERVER_ERROR',

  /** SSE 串流錯誤 */
  STREAM_ERROR: 'STREAM_ERROR',

  /** 未知錯誤 */
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const

// eslint-disable-next-line ts/no-redeclare
export type ChatErrorType = typeof ChatErrorType[keyof typeof ChatErrorType]

/** 分類後的錯誤資訊 */
export interface ClassifiedError {
  type: ChatErrorType
  message: string
  userMessage: string // 使用者友善訊息
  originalError?: Error | unknown
}
