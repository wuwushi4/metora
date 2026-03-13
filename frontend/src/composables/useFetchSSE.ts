import type { MessageChunk } from '@/types/chat'
import { fetchEventSource } from '@microsoft/fetch-event-source'
/**
 * fetch-event-source Composable
 * 提供通用的 SSE 串流處理功能
 */
import { onUnmounted, ref } from 'vue'
import i18n from '@/i18n'

const { t } = i18n.global

export function useFetchSSE() {
  const abortController = ref<AbortController | null>(null)
  const isStreaming = ref(false)
  const error = ref<string | null>(null)

  /**
   * 發送 SSE 串流請求
   *
   * @param url API 端點 (相對路徑,如 '/v1/chat/sessions/xxx/messages')
   * @param body 請求 body
   * @param onMessage 接收訊息的回調函數
   * @param onMetadata 接收 metadata 的回調函數 (可選)
   */
  async function streamRequest(
    url: string,
    body: any,
    onMessage: (data: any) => void,
    onMetadata?: (metadata: any) => void,
  ) {
    // 取消舊請求
    cancelStream()

    abortController.value = new AbortController()
    isStreaming.value = true
    error.value = null

    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const fullURL = `${baseURL}${url}`

    try {
      await fetchEventSource(fullURL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        credentials: 'include', // 發送 cookies (對應 withCredentials: true)
        signal: abortController.value.signal,

        async onopen(res) {
          if (res.ok) {
            // 連接成功

          }
          else if (res.status >= 400 && res.status < 500) {
            // 客戶端錯誤 (4xx) - 不重試
            const errorText = await res.text()
            throw new Error(`客戶端錯誤 ${res.status}: ${errorText}`)
          }
          else {
            // 伺服器錯誤 (5xx) - 會自動重試
            throw new Error(`伺服器錯誤 ${res.status}`)
          }
        },

        onmessage(event) {
          if (event.data === '[DONE]') {
            isStreaming.value = false
            return
          }

          try {
            const chunk: MessageChunk = JSON.parse(event.data)

            // 根據訊息類型分發
            if (chunk.type === 'token') {
              // LLM token 串流（逐字輸出）
              onMessage(chunk)
            }
            else if (chunk.type === 'metadata') {
              // 中間節點資訊 (檢索結果、意圖判別等)
              if (onMetadata) {
                onMetadata(chunk)
              }
            }
            else if (chunk.type === 'node_start' || chunk.type === 'node_end') {
              // 節點開始/結束事件,可選擇性處理
              if (onMetadata) {
                onMetadata(chunk)
              }
            }
            else if (chunk.type === 'tool_call' || chunk.type === 'tool_result') {
              // Agent 工具呼叫/結果事件
              if (onMetadata) {
                onMetadata(chunk)
              }
            }
            else if (chunk.type === 'done') {
              // 串流完成
              onMessage(chunk)
              isStreaming.value = false
            }
            else if (chunk.type === 'error') {
              // 錯誤訊息
              error.value = chunk.content
              isStreaming.value = false
              throw new Error(chunk.content)
            }
            else {
              // 其他未知類型
              console.warn('未知的 SSE 訊息類型:', chunk)
            }
          }
          catch (e) {
            if (e instanceof Error && e.message.startsWith('客戶端錯誤')) {
              throw e
            }
            console.error('解析 SSE 資料失敗:', event.data, e)
          }
        },

        onerror(err) {
          // 處理錯誤
          if (err instanceof Error) {
            error.value = err.message

            // 401 錯誤特殊處理 (會被 request interceptor 處理,這裡不重試)
            if (err.message.includes('401')) {
              isStreaming.value = false
              throw err
            }

            // 客戶端錯誤不重試
            if (err.message.includes('客戶端錯誤')) {
              isStreaming.value = false
              throw err
            }
          }
          else {
            error.value = t('errors.unknown')
          }

          isStreaming.value = false
          throw err
        },
      })
    }
    catch (e) {
      // AbortError 是正常的取消操作,不視為錯誤
      if (e instanceof Error && e.name !== 'AbortError') {
        error.value = e.message
        console.error('SSE 串流錯誤:', e)
      }
    }
    finally {
      isStreaming.value = false
    }
  }

  /**
   * 取消當前串流
   */
  function cancelStream() {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
    isStreaming.value = false
  }

  // 組件卸載時自動取消串流
  onUnmounted(() => {
    cancelStream()
  })

  return {
    isStreaming,
    error,
    streamRequest,
    cancelStream,
  }
}
