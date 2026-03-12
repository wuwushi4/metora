/**
 * 搜尋歷史管理 Composable
 *
 * 使用 LocalStorage 儲存搜尋歷史記錄
 */
import { useLocalStorage } from '@vueuse/core'

// 常量定義
const STORAGE_KEY = 'chat_search_history'
const MAX_HISTORY = 10

/**
 * 搜尋歷史管理
 *
 * 提供搜尋歷史的增刪改查功能，自動同步到 LocalStorage
 *
 * @returns 搜尋歷史管理方法
 *
 * @example
 * ```typescript
 * const { history, addHistory, removeHistory, clearHistory } = useSearchHistory()
 *
 * // 添加搜尋記錄
 * addHistory('法規')
 *
 * // 顯示歷史記錄
 * console.log(history.value) // ['法規', ...]
 *
 * // 刪除單筆記錄
 * removeHistory('法規')
 *
 * // 清空所有記錄
 * clearHistory()
 * ```
 */
export function useSearchHistory() {
  // 使用 useLocalStorage 自動處理 LocalStorage 同步
  // 包含資料驗證和錯誤處理
  const history = useLocalStorage<string[]>(
    STORAGE_KEY,
    [],
    {
      // 自訂序列化器，包含資料驗證
      serializer: {
        read: (raw: string) => {
          try {
            const parsed = JSON.parse(raw)
            // 驗證資料格式
            if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
              // 限制數量
              return parsed.slice(0, MAX_HISTORY)
            }
            return []
          }
          catch (error) {
            console.error('載入搜尋歷史失敗:', error)
            return []
          }
        },
        write: (value: string[]) => JSON.stringify(value),
      },
    },
  )

  /**
   * 添加搜尋記錄
   *
   * @param query - 搜尋關鍵字
   */
  function addHistory(query: string) {
    const trimmed = query.trim()
    if (!trimmed)
      return

    // 移除重複項（不分大小寫）
    history.value = history.value.filter(
      item => item.toLowerCase() !== trimmed.toLowerCase(),
    )

    // 新增到開頭
    history.value.unshift(trimmed)

    // 限制數量
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(0, MAX_HISTORY)
    }
  }

  /**
   * 刪除單筆記錄
   *
   * @param query - 要刪除的關鍵字
   */
  function removeHistory(query: string) {
    history.value = history.value.filter(item => item !== query)
  }

  /**
   * 清空所有歷史記錄
   */
  function clearHistory() {
    history.value = []
  }

  /**
   * 檢查關鍵字是否在歷史記錄中
   *
   * @param query - 搜尋關鍵字
   * @returns 是否存在
   */
  function hasHistory(query: string): boolean {
    const trimmed = query.trim().toLowerCase()
    return history.value.some(item => item.toLowerCase() === trimmed)
  }

  return {
    history,
    addHistory,
    removeHistory,
    clearHistory,
    hasHistory,
  }
}
