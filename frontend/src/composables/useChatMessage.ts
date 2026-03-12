import type { Ref } from 'vue'
import type { ChatMessage, ChunkMetadata, MessageChunk } from '@/types/chat'
import type { ClassifiedError } from '@/types/error'
import { fetchEventSource } from '@microsoft/fetch-event-source'
/**
 * Chat 訊息發送 Composable
 * 處理訊息發送邏輯和串流回應
 */
import { ref } from 'vue'
import { savePartialMessage as savePartialMessageAPI } from '@/api/chat'
import { ChatErrorType } from '@/types/error'
import { createMessageFormData } from '@/utils/fileUtils'

/**
 * 分類錯誤
 */
function classifyError(error: unknown, statusCode?: number): ClassifiedError {
  // 網路錯誤
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      type: ChatErrorType.NETWORK_ERROR,
      message: '網路連線失敗',
      userMessage: '無法連接到伺服器，請檢查網路連線',
      originalError: error,
    }
  }

  // HTTP 狀態碼分類
  if (statusCode) {
    // 認證錯誤
    if (statusCode === 401 || statusCode === 403) {
      return {
        type: ChatErrorType.AUTHENTICATION_ERROR,
        message: `認證失敗 (${statusCode})`,
        userMessage: '登入已過期，請重新登入',
        originalError: error,
      }
    }

    // 檔案上傳錯誤 (從錯誤訊息判斷)
    const errorMsg = error instanceof Error ? error.message : String(error)
    if (statusCode === 400 && (
      errorMsg.includes('檔案')
      || errorMsg.includes('上傳')
      || errorMsg.includes('大小')
      || errorMsg.includes('格式')
    )) {
      return {
        type: ChatErrorType.FILE_UPLOAD_ERROR,
        message: errorMsg,
        userMessage: errorMsg, // 檔案錯誤訊息已經很明確
        originalError: error,
      }
    }

    // 一般驗證錯誤
    if (statusCode >= 400 && statusCode < 500) {
      return {
        type: ChatErrorType.VALIDATION_ERROR,
        message: errorMsg,
        userMessage: errorMsg,
        originalError: error,
      }
    }

    // 伺服器錯誤
    if (statusCode >= 500) {
      return {
        type: ChatErrorType.SERVER_ERROR,
        message: `伺服器錯誤 (${statusCode})`,
        userMessage: '伺服器發生錯誤，請稍後再試',
        originalError: error,
      }
    }
  }

  // SSE 串流錯誤 (從 error chunk)
  const errorMsg = error instanceof Error ? error.message : String(error)
  if (errorMsg.includes('串流')) {
    return {
      type: ChatErrorType.STREAM_ERROR,
      message: errorMsg,
      userMessage: errorMsg,
      originalError: error,
    }
  }

  // 未知錯誤
  return {
    type: ChatErrorType.UNKNOWN_ERROR,
    message: errorMsg,
    userMessage: '發生未知錯誤，請稍後再試',
    originalError: error,
  }
}

export function useChatMessage(sessionIdRef: Ref<string>) {
  const abortController = ref<AbortController | null>(null)
  const isStreaming = ref(false)
  const error = ref<string | null>(null)

  const currentMessage = ref<ChatMessage | null>(null)
  const tempContent = ref('')
  const currentMetadata = ref<ChunkMetadata>({})

  /**
   * 發送訊息（支援檔案上傳和提示詞模板）
   *
   * @param content 訊息內容
   * @param files 檔案列表（可選）
   * @param onComplete 完成時的回調 (接收完整的 assistant 訊息)
   * @param onProgress 進度回調 (接收當前累積的內容)
   * @param onUserMessage 使用者訊息回調 (接收完整的 user 訊息，包含附件)
   * @param promptTemplateId 提示詞模板 ID（可選）
   */
  async function sendMessage(
    content: string,
    files: File[] = [],
    onComplete?: (message: ChatMessage) => void,
    onProgress?: (content: string, metadata: ChunkMetadata) => void,
    onUserMessage?: (message: ChatMessage) => void,
    promptTemplateId?: string | null,
  ) {
    const sessionId = sessionIdRef.value

    if (!sessionId) {
      throw new Error('Session ID 不能為空')
    }

    // 取消舊請求
    if (abortController.value) {
      abortController.value.abort()
    }

    abortController.value = new AbortController()
    isStreaming.value = true
    error.value = null
    tempContent.value = ''
    currentMetadata.value = {}

    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const fullURL = `${baseURL}/v1/chat/sessions/${sessionId}/messages`

    // 準備請求 body（包含提示詞模板 ID）
    const formData = createMessageFormData(content, files, promptTemplateId)

    try {
      await fetchEventSource(fullURL, {
        method: 'POST',
        body: formData,
        credentials: 'include',
        signal: abortController.value.signal,
        openWhenHidden: true,

        async onopen(res) {
          if (res.ok) {
            return
          }
          const errorText = await res.text()
          const classified = classifyError(new Error(errorText), res.status)
          error.value = classified.userMessage
          throw new Error(classified.userMessage)
        },

        onmessage(event) {
          if (event.data === '[DONE]') {
            isStreaming.value = false
            return
          }

          try {
            const chunk: MessageChunk = JSON.parse(event.data)

            if (chunk.type === 'user_message') {
              // 收到使用者訊息（包含附件）- 透過回調傳給父組件
              if (chunk.message && onUserMessage) {
                onUserMessage(chunk.message)
              }
            }
            else if (chunk.type === 'token') {
              tempContent.value += chunk.content

              if (onProgress) {
                onProgress(tempContent.value, currentMetadata.value)
              }
            }
            else if (chunk.type === 'metadata') {
              currentMetadata.value = {
                ...currentMetadata.value,
                ...chunk.data,
              }

              if (onProgress) {
                onProgress(tempContent.value, currentMetadata.value)
              }
            }
            else if (chunk.type === 'node_start' || chunk.type === 'node_end') {
              // 節點事件,可選擇性處理
            }
            else if (chunk.type === 'tool_call') {
              // Agent 工具呼叫事件 - 將程式碼區塊注入訊息內容
              const toolName = chunk.data.tool_name || 'tool'
              const args = chunk.data.args || {}
              const code = args.code || ''

              // 注入可摺疊的程式碼區塊（使用 HTML details 標籤）
              if (code) {
                tempContent.value += `\n\n<details open>\n<summary>🔧 ${toolName}</summary>\n\n\`\`\`python\n${code}\n\`\`\`\n\n⏳ 執行中...\n</details>\n\n`
              }
              else {
                tempContent.value += `\n\n🔧 呼叫工具: ${toolName}...\n\n`
              }

              // 同時存入 metadata
              const toolCalls = currentMetadata.value.tool_calls || []
              toolCalls.push({
                tool_name: toolName,
                tool_call_id: chunk.data.tool_call_id,
                code,
              })
              currentMetadata.value = {
                ...currentMetadata.value,
                tool_calls: toolCalls,
              }

              if (onProgress) {
                onProgress(tempContent.value, currentMetadata.value)
              }
            }
            else if (chunk.type === 'tool_result') {
              // Agent 工具結果事件 - 替換「執行中」為實際結果
              const resultContent = chunk.data.content || ''
              const outputFiles = chunk.data.output_files || []

              // 替換最後一個「⏳ 執行中...」為實際結果
              const placeholder = '⏳ 執行中...'
              const lastIdx = tempContent.value.lastIndexOf(placeholder)
              if (lastIdx !== -1) {
                const resultBlock = `\`\`\`\n${resultContent}\n\`\`\``
                tempContent.value
                  = tempContent.value.substring(0, lastIdx)
                  + resultBlock
                  + tempContent.value.substring(lastIdx + placeholder.length)
              }
              else {
                // fallback：直接追加結果
                tempContent.value += `\n\`\`\`\n${resultContent}\n\`\`\`\n\n`
              }

              // 存入 metadata
              const toolResults = currentMetadata.value.tool_results || []
              toolResults.push({
                tool_name: chunk.data.tool_name,
                content: resultContent,
                output_files: outputFiles,
              })
              currentMetadata.value = {
                ...currentMetadata.value,
                tool_results: toolResults,
              }

              if (onProgress) {
                onProgress(tempContent.value, currentMetadata.value)
              }
            }
            else if (chunk.type === 'done') {
              const message: ChatMessage = {
                id: chunk.data.message_id,
                session_id: sessionId,
                role: 'assistant',
                content: tempContent.value,
                metadata: {
                  ...currentMetadata.value,
                  ...chunk.data,
                },
                created_at: new Date().toISOString(),
              }

              currentMessage.value = message
              isStreaming.value = false

              if (onComplete) {
                onComplete(message)
              }
            }
            else if (chunk.type === 'error') {
              error.value = chunk.content
              isStreaming.value = false
              // 不拋出錯誤，讓 watch(error) 統一處理顯示
            }
          }
          catch (e) {
            console.error('解析 SSE 資料失敗:', event.data, e)
          }
        },

        onerror(err) {
          const classified = classifyError(err)
          error.value = classified.userMessage
          isStreaming.value = false
          // 不拋出錯誤，讓 watch(error) 統一處理顯示
        },
      })
    }
    catch (e) {
      if (e instanceof Error && e.name !== 'AbortError') {
        const classified = classifyError(e)
        error.value = classified.userMessage
        console.error(`[${classified.type}]`, classified.message, classified.originalError)
      }
    }
    finally {
      isStreaming.value = false
    }
  }

  /**
   * 取消當前串流
   *
   * @param savePartial 是否保存已經輸出的部分內容
   * @returns 如果保存成功，返回保存後的完整訊息
   */
  async function cancelStream(savePartial = false): Promise<ChatMessage | null> {
    // 中斷 SSE 連接
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
    isStreaming.value = false

    // 如果需要保存部分內容且有內容
    if (savePartial && tempContent.value.trim()) {
      const sessionId = sessionIdRef.value
      if (!sessionId) {
        console.warn('無法保存部分訊息：Session ID 不存在')
        return null
      }

      try {
        const savedMessage = await savePartialMessageAPI(
          sessionId,
          tempContent.value,
          currentMetadata.value,
        )
        return savedMessage
      }
      catch (err) {
        console.error('保存部分訊息失敗:', err)
        error.value = '保存部分訊息失敗'
        return null
      }
    }

    return null
  }

  /**
   * 保存部分訊息
   *
   * 獨立的方法，用於在不中斷串流的情況下保存部分內容
   */
  async function savePartialMessage(
    content: string,
    metadata: ChunkMetadata,
  ): Promise<ChatMessage | null> {
    const sessionId = sessionIdRef.value
    if (!sessionId) {
      throw new Error('Session ID 不能為空')
    }

    try {
      const savedMessage = await savePartialMessageAPI(sessionId, content, metadata)
      return savedMessage
    }
    catch (err) {
      error.value = '保存部分訊息失敗'
      throw err
    }
  }

  return {
    isStreaming,
    error,
    currentMessage,
    tempContent,
    currentMetadata,
    sendMessage,
    cancelStream,
    savePartialMessage,
  }
}
