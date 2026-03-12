import type { ChatMessage, ChatSession, GraphInfo, SessionCreateRequest } from '@/types/chat'
import type { Feedback } from '@/types/feedback'
import type { FilePreview } from '@/types/upload'
/**
 * Chat Store
 * 管理 Session 和訊息的狀態
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as chatApi from '@/api/chat'
import { revokeFilePreview } from '@/utils/fileUtils'
import { message } from '@/utils/message'

export const useChatStore = defineStore('chat', () => {
  // ==================== State ====================

  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<ChatMessage[]>([])
  const graphs = ref<GraphInfo[]>([])

  // 附件狀態
  const pendingFiles = ref<FilePreview[]>([])

  // 提示詞模板狀態
  const selectedPromptTemplateId = ref<string | null>(null)

  // 細分 loading 狀態
  const loadingStates = ref({
    sessions: false,
    messages: false,
    creating: false,
    sending: false,
  })

  // ==================== Getters ====================

  const hasCurrentSession = computed(() => !!currentSession.value)

  const isLoading = computed(() =>
    Object.values(loadingStates.value).some(v => v),
  )

  const isSending = computed(() => loadingStates.value.sending)

  const hasPendingFiles = computed(() => pendingFiles.value.length > 0)

  const hasSelectedPrompt = computed(() => !!selectedPromptTemplateId.value)

  // ==================== Actions ====================

  /**
   * 載入所有可用的 Graph
   */
  async function loadGraphs() {
    try {
      graphs.value = await chatApi.getGraphs()
    }
    catch (error) {
      console.error('載入 Graphs 失敗:', error)
      message.error('載入 Graph 列表失敗')
    }
  }

  /**
   * 載入使用者的 Sessions
   */
  async function loadSessions() {
    loadingStates.value.sessions = true
    try {
      const response = await chatApi.getSessions({
        page: 1,
        pageSize: 100,
        is_active: true,
      })
      sessions.value = response.items
    }
    catch (error) {
      console.error('載入 Sessions 失敗:', error)
      message.error('載入會話列表失敗')
      throw error
    }
    finally {
      loadingStates.value.sessions = false
    }
  }

  /**
   * 建立新的 Session
   */
  async function createNewSession(request: SessionCreateRequest) {
    loadingStates.value.creating = true
    try {
      const newSession = await chatApi.createSession(request)
      sessions.value.unshift(newSession)
      currentSession.value = newSession
      messages.value = []

      message.success('建立會話成功')
      return newSession
    }
    catch (error) {
      console.error('建立 Session 失敗:', error)
      message.error('建立會話失敗')
      throw error
    }
    finally {
      loadingStates.value.creating = false
    }
  }

  /**
   * 切換到指定的 Session
   */
  async function switchSession(sessionId: string) {
    try {
      const session = await chatApi.getSessionById(sessionId)
      currentSession.value = session

      // 載入訊息
      await loadMessages(sessionId)
    }
    catch (error) {
      console.error('切換 Session 失敗:', error)
      message.error('切換會話失敗')
      throw error
    }
  }

  /**
   * 載入 Session 的歷史訊息
   */
  async function loadMessages(sessionId: string) {
    loadingStates.value.messages = true
    try {
      const response = await chatApi.getMessages(sessionId, {
        page: 1,
        pageSize: 100,
      })
      messages.value = response.items
    }
    catch (error) {
      console.error('載入訊息失敗:', error)
      message.error('載入訊息失敗')
    }
    finally {
      loadingStates.value.messages = false
    }
  }

  /**
   * 重命名 Session
   */
  async function renameSession(sessionId: string, title: string) {
    try {
      const updated = await chatApi.updateSession(sessionId, { title })

      // 更新本地狀態
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = updated
      }

      if (currentSession.value?.id === sessionId) {
        currentSession.value = updated
      }

      message.success('重命名成功')
    }
    catch (error) {
      console.error('重命名失敗:', error)
      message.error('重命名失敗')
      throw error
    }
  }

  /**
   * 刪除 Session
   */
  async function removeSession(sessionId: string) {
    try {
      await chatApi.deleteSession(sessionId)

      // 移除本地狀態
      sessions.value = sessions.value.filter(s => s.id !== sessionId)

      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
        messages.value = []
      }

      message.success('刪除成功')
    }
    catch (error) {
      console.error('刪除 Session 失敗:', error)
      message.error('刪除會話失敗')
      throw error
    }
  }

  /**
   * 添加使用者訊息（樂觀更新）
   */
  function addUserMessage(content: string, attachments?: any[]): ChatMessage {
    if (!currentSession.value) {
      throw new Error('沒有選擇的 Session')
    }

    const userMessage: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      session_id: currentSession.value.id,
      role: 'user',
      content,
      metadata: {},
      created_at: new Date().toISOString(),
      attachments,
    }

    messages.value.push(userMessage)
    return userMessage
  }

  /**
   * 添加 assistant 訊息
   */
  function addAssistantMessage(message: ChatMessage) {
    messages.value.push(message)

    // 更新 Session 的 message_count
    if (currentSession.value) {
      currentSession.value.message_count = (currentSession.value.message_count || 0) + 2
    }
  }

  /**
   * 更新正在串流的訊息內容
   */
  function updateStreamingMessage(tempId: string, content: string, metadata: any) {
    const index = messages.value.findIndex(m => m.id === tempId)
    if (index !== -1) {
      const message = messages.value[index]
      if (message) {
        message.content = content
        message.metadata = metadata
      }
    }
    else {
      // 如果還沒有臨時訊息,創建一個
      if (currentSession.value) {
        messages.value.push({
          id: tempId,
          session_id: currentSession.value.id,
          role: 'assistant',
          content,
          metadata,
          created_at: new Date().toISOString(),
        })
      }
    }
  }

  /**
   * 替換臨時訊息為真實訊息
   */
  function replaceTempMessage(tempId: string, realMessage: ChatMessage) {
    const index = messages.value.findIndex(m => m.id === tempId)
    if (index !== -1) {
      messages.value[index] = realMessage
    }
  }

  /**
   * 移除訊息（用於錯誤回滾）
   */
  function removeMessage(messageId: string) {
    messages.value = messages.value.filter(m => m.id !== messageId)
  }

  /**
   * 設定發送狀態
   */
  function setSendingState(sending: boolean) {
    loadingStates.value.sending = sending
  }

  /**
   * 清除當前 Session
   */
  function clearCurrentSession() {
    currentSession.value = null
    messages.value = []
  }

  /**
   * 更新訊息的反饋
   */
  function updateMessageFeedback(messageId: string, feedback: Feedback) {
    const messageIndex = messages.value.findIndex(m => m.id === messageId)
    if (messageIndex !== -1) {
      const targetMessage = messages.value[messageIndex]
      if (targetMessage) {
        targetMessage.user_feedback = feedback
      }
    }
  }

  /**
   * 添加待發送的檔案
   */
  function addPendingFiles(files: FilePreview[]) {
    pendingFiles.value.push(...files)
  }

  /**
   * 移除待發送的檔案
   */
  function removePendingFile(fileId: string) {
    const file = pendingFiles.value.find(f => f.id === fileId)
    if (file) {
      revokeFilePreview(file)
    }
    pendingFiles.value = pendingFiles.value.filter(f => f.id !== fileId)
  }

  /**
   * 清空待發送的檔案
   */
  function clearPendingFiles() {
    pendingFiles.value.forEach(file => revokeFilePreview(file))
    pendingFiles.value = []
  }

  /**
   * 更新待發送檔案的狀態
   */
  function updatePendingFileStatus(
    fileId: string,
    status: FilePreview['status'],
    error?: string,
  ) {
    const file = pendingFiles.value.find(f => f.id === fileId)
    if (file) {
      file.status = status
      if (error) {
        file.error = error
      }
    }
  }

  /**
   * 選擇提示詞模板
   */
  function selectPromptTemplate(templateId: string | null) {
    selectedPromptTemplateId.value = templateId
  }

  /**
   * 清除選擇的提示詞模板
   */
  function clearPromptTemplate() {
    selectedPromptTemplateId.value = null
  }

  /**
   * 重置所有聊天狀態（用於登出）
   */
  function resetStore() {
    // 清除待發送檔案的 blob URL
    pendingFiles.value.forEach(file => revokeFilePreview(file))

    // 重置所有狀態
    sessions.value = []
    currentSession.value = null
    messages.value = []
    graphs.value = []
    pendingFiles.value = []
    selectedPromptTemplateId.value = null
    loadingStates.value = {
      sessions: false,
      messages: false,
      creating: false,
      sending: false,
    }
  }

  // ==================== Return ====================

  return {
    // State
    sessions,
    currentSession,
    messages,
    graphs,
    loadingStates,
    pendingFiles,
    selectedPromptTemplateId,

    // Getters
    hasCurrentSession,
    isLoading,
    isSending,
    hasPendingFiles,
    hasSelectedPrompt,

    // Actions
    loadGraphs,
    loadSessions,
    createNewSession,
    switchSession,
    loadMessages,
    renameSession,
    removeSession,
    addUserMessage,
    addAssistantMessage,
    updateStreamingMessage,
    replaceTempMessage,
    removeMessage,
    setSendingState,
    clearCurrentSession,
    updateMessageFeedback,
    addPendingFiles,
    removePendingFile,
    clearPendingFiles,
    updatePendingFileStatus,
    selectPromptTemplate,
    clearPromptTemplate,
    resetStore,
  }
})
