/**
 * 錯誤處理工具模組
 * 提供統一的錯誤處理和使用者提示機制
 */

import type { AxiosError } from 'axios'
import type { ApiError } from '@/types/api'
import i18n from '@/i18n'

const { t } = i18n.global

/**
 * 錯誤處理選項
 */
interface ErrorHandlerOptions {
  /** 是否顯示錯誤訊息 (預設: true) */
  showMessage?: boolean
  /** 自訂錯誤訊息 */
  customMessage?: string
  /** 是否在 401 時自動重導向到登入頁 (預設: true) */
  redirectOnUnauthorized?: boolean
  /** 錯誤回調函數 */
  onError?: (error: any) => void
}

/**
 * 錯誤訊息映射表（動態取得 i18n 翻譯）
 */
function getErrorMessages(): Record<number, string> {
  return {
    400: t('errors.http.400'),
    401: t('errors.http.401'),
    403: t('errors.http.403'),
    404: t('errors.http.404'),
    408: t('errors.http.408'),
    500: t('errors.http.500'),
    502: t('errors.http.502'),
    503: t('errors.http.503'),
    504: t('errors.http.504'),
  }
}

/**
 * 解析 API 錯誤
 */
function parseApiError(error: AxiosError): { status: number, message: string, details?: ApiError } {
  const ERROR_MESSAGES = getErrorMessages()

  if (error.response) {
    // 伺服器返回錯誤響應
    const status = error.response.status
    const data = error.response.data as ApiError | undefined

    const message = data?.message
      || ERROR_MESSAGES[status]
      || t('errors.requestFailed', { status })

    return {
      status,
      message,
      details: data,
    }
  }
  else if (error.request) {
    // 請求已發送但沒有收到響應
    if (error.code === 'ECONNABORTED') {
      return {
        status: 408,
        message: t('errors.timeout'),
      }
    }
    return {
      status: 0,
      message: t('errors.network'),
    }
  }
  else {
    // 請求配置出錯
    return {
      status: -1,
      message: error.message || t('errors.configError'),
    }
  }
}

/**
 * 處理 API 錯誤
 *
 * 注意: 這個函數返回錯誤資訊,但不直接顯示訊息
 * 實際的訊息顯示會在 request.ts 的攔截器中處理
 *
 * @param error - Axios 錯誤物件
 * @param options - 錯誤處理選項
 * @returns 解析後的錯誤資訊
 */
export function handleApiError(error: any, options: ErrorHandlerOptions = {}) {
  const {
    showMessage = true,
    customMessage,
    redirectOnUnauthorized = true,
    onError,
  } = options

  // 解析錯誤
  const errorInfo = parseApiError(error)

  // 最終顯示的訊息
  const finalMessage = customMessage || errorInfo.message

  // 執行錯誤回調
  if (onError) {
    onError(errorInfo)
  }

  // 返回錯誤資訊供攔截器使用
  return {
    ...errorInfo,
    message: finalMessage,
    showMessage,
    redirectOnUnauthorized,
  }
}

/**
 * 格式化驗證錯誤
 * 將後端返回的欄位驗證錯誤格式化為使用者友善的訊息
 *
 * @param errors - 欄位驗證錯誤物件
 * @returns 格式化後的錯誤訊息
 */
export function formatValidationErrors(errors: Record<string, string[]>): string {
  const messages: string[] = []

  for (const [field, fieldErrors] of Object.entries(errors)) {
    if (fieldErrors && fieldErrors.length > 0) {
      messages.push(`${field}: ${fieldErrors.join(', ')}`)
    }
  }

  return messages.join('\n')
}

/**
 * 判斷是否為網路錯誤
 */
export function isNetworkError(error: any): boolean {
  return !error.response && error.request
}

/**
 * 判斷是否為超時錯誤
 */
export function isTimeoutError(error: any): boolean {
  return error.code === 'ECONNABORTED' || error.message?.includes('timeout')
}

/**
 * 判斷是否為認證錯誤
 */
export function isAuthError(error: any): boolean {
  return error.response?.status === 401
}

/**
 * 判斷是否為權限錯誤
 */
export function isPermissionError(error: any): boolean {
  return error.response?.status === 403
}

/**
 * 獲取錯誤訊息
 * 從錯誤物件中提取可讀的錯誤訊息
 */
export function getErrorMessage(error: any): string {
  if (typeof error === 'string') {
    return error
  }

  if (error?.response?.data?.message) {
    return error.response.data.message
  }

  if (error?.message) {
    return error.message
  }

  return t('errors.unknown')
}
