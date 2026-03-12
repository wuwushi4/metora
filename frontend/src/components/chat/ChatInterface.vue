<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useChatMessage } from '@/composables/useChatMessage'
import { useChatStore } from '@/stores/chat'
import { message as messageApi } from '@/utils/message'
import EmptyChat from './EmptyChat.vue'
import MessageInput from './MessageInput.vue'
import MessageList from './MessageList.vue'

const chatStore = useChatStore()

// 當前 Session
const currentSession = computed(() => chatStore.currentSession)
const messages = computed(() => chatStore.messages)
const isSending = computed(() => chatStore.isSending)
const selectedPromptId = computed(() => chatStore.selectedPromptTemplateId)

// 訊息發送 composable
const sessionId = computed(() => currentSession.value?.id || '')
const { isStreaming, error, tempContent, sendMessage, cancelStream } = useChatMessage(sessionId)

// 臨時訊息 ID (用於串流更新)
const tempMessageId = ref<string | null>(null)

// 是否有訊息
const hasMessages = computed(() => messages.value.length > 0)

// 監聽 Session 切換，清空待發送檔案
watch(
  () => currentSession.value?.id,
  (newSessionId, oldSessionId) => {
    if (newSessionId !== oldSessionId && oldSessionId !== undefined) {
      // 切換 Session 時清空待發送檔案
      chatStore.clearPendingFiles()

      // 如果有臨時訊息，也一併清除
      if (tempMessageId.value) {
        chatStore.removeMessage(tempMessageId.value)
        tempMessageId.value = null
      }
    }
  },
)

// 處理發送訊息（支援檔案上傳）
async function handleSendMessage(content: string, files: File[] = []) {
  if (!currentSession.value) {
    messageApi.warning('請先選擇或建立一個對話')
    return
  }

  if (!content.trim() && files.length === 0) {
    return
  }

  // 不樂觀更新使用者訊息，等待後端回傳（避免閃爍和競態條件）
  // 設定發送狀態
  chatStore.setSendingState(true)

  // 生成臨時 ID
  tempMessageId.value = `temp-assistant-${Date.now()}`

  try {
    await sendMessage(
      content,
      files,
      // 完成回調
      (assistantMessage) => {
        // 替換臨時訊息為真實訊息
        if (tempMessageId.value) {
          chatStore.replaceTempMessage(tempMessageId.value, assistantMessage)
        }
        else {
          chatStore.addAssistantMessage(assistantMessage)
        }

        // 清除臨時 ID
        tempMessageId.value = null

        // 重置發送狀態
        chatStore.setSendingState(false)
      },
      // 進度回調
      (streamContent, metadata) => {
        // 更新串流中的訊息
        if (tempMessageId.value) {
          chatStore.updateStreamingMessage(tempMessageId.value, streamContent, metadata)
        }
      },
      // 使用者訊息回調（包含附件）
      (userMessage) => {
        // 直接添加後端返回的完整使用者訊息（包含真實 ID 和附件）
        chatStore.messages.push(userMessage)
      },
      // 提示詞模板 ID
      selectedPromptId.value,
    )
  }
  catch (err) {
    console.error('發送訊息失敗:', err)

    // 移除臨時 assistant 訊息
    if (tempMessageId.value) {
      chatStore.removeMessage(tempMessageId.value)
      tempMessageId.value = null
    }

    // 重置發送狀態
    chatStore.setSendingState(false)

    // 錯誤訊息由 watch(error) 統一處理，避免重複顯示
  }
}

// 處理選擇示例問題
function handleSelectExample(question: string) {
  handleSendMessage(question)
}

// 處理停止
async function handleStop() {
  if (!isStreaming.value) {
    return
  }

  // 中斷串流並保存部分內容
  const savedMessage = await cancelStream(true)

  if (savedMessage && tempMessageId.value) {
    // 用真實訊息替換臨時訊息
    chatStore.replaceTempMessage(tempMessageId.value, savedMessage)
    tempMessageId.value = null
  }
  else if (tempMessageId.value) {
    // 如果保存失敗但有臨時訊息，移除臨時訊息
    if (tempContent.value.trim() === '') {
      // 沒有內容，直接移除
      chatStore.removeMessage(tempMessageId.value)
    }
    else {
      // 有內容但保存失敗，保留臨時訊息作為本地記錄
      // 註：這個訊息沒有真實的 message_id，無法進行反饋
      console.warn('保存部分訊息失敗，保留本地臨時訊息')
    }
    tempMessageId.value = null
  }

  // 重置發送狀態
  chatStore.setSendingState(false)
}

// 監聽錯誤 - 根據錯誤類型調整顯示方式並智能清理狀態
watch(error, (newError) => {
  if (newError) {
    // 智能處理臨時訊息：
    // - 如果沒有內容輸出（如檔案處理失敗），移除臨時訊息
    // - 如果有內容輸出（如中斷或 LLM 錯誤），保留已輸出內容，轉為正式訊息
    if (tempMessageId.value) {
      if (tempContent.value.trim() === '') {
        // 沒有內容，直接移除
        chatStore.removeMessage(tempMessageId.value)
        tempMessageId.value = null
      }
      else {
        // 有內容，轉為正式訊息（保留已輸出的內容）
        const partialMessage = {
          id: tempMessageId.value,
          session_id: currentSession.value!.id,
          role: 'assistant' as const,
          content: tempContent.value,
          metadata: {},
          created_at: new Date().toISOString(),
        }
        chatStore.replaceTempMessage(tempMessageId.value, partialMessage)
        tempMessageId.value = null
      }
    }

    // 重置發送狀態（無論如何都要重置）
    chatStore.setSendingState(false)

    // 顯示錯誤訊息 - 根據錯誤類型調整顯示方式
    if (newError.includes('檔案') || newError.includes('上傳')) {
      messageApi.warning(newError, { duration: 5000 })
    }
    else {
      messageApi.error(newError, { duration: 5000 })
    }
  }
})

// 監聽 Session 變更,重新建立 composable
watch(() => currentSession.value?.id, (newSessionId) => {
  if (newSessionId) {
    // Session 變更時,清除臨時訊息
    if (tempMessageId.value) {
      chatStore.removeMessage(tempMessageId.value)
      tempMessageId.value = null
    }
  }
})
</script>

<template>
  <div class="chat-interface">
    <!-- 訊息區域 -->
    <div class="messages-area">
      <!-- 空狀態 -->
      <EmptyChat
        v-if="!hasMessages"
        :graph-type="currentSession?.graph_type || null"
        @select-example="handleSelectExample"
      />

      <!-- 訊息列表 -->
      <MessageList
        v-else
        :messages="messages"
        :loading="chatStore.loadingStates.messages"
        :streaming="isStreaming || isSending"
      />
    </div>

    <!-- 輸入區域 -->
    <div class="input-area">
      <MessageInput
        :disabled="!currentSession || isStreaming || isSending"
        :loading="isStreaming || isSending"
        @send="handleSendMessage"
        @stop="handleStop"
      />
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 訊息區域 */
.messages-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border: 2px solid transparent;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7)),
    linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(99, 102, 241, 0.25) 50%, rgba(139, 92, 246, 0.25) 100%);
  background-origin: padding-box, border-box;
  background-clip: padding-box, border-box;
  box-shadow:
    0 4px 16px rgba(14, 165, 233, 0.08),
    0 2px 8px rgba(139, 92, 246, 0.06),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  margin: 0;
  position: relative;
}

/* 頂部精緻裝飾線 */
.messages-area::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    rgba(14, 165, 233, 0.5) 0%,
    rgba(99, 102, 241, 0.5) 50%,
    rgba(139, 92, 246, 0.5) 100%
  );
  border-radius: 12px 12px 0 0;
}

/* 輸入區域 */
.input-area {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 2px solid transparent;
  border-top: none;
  border-radius: 0 0 12px 12px;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)),
    linear-gradient(135deg, rgba(14, 165, 233, 0.3) 0%, rgba(99, 102, 241, 0.3) 50%, rgba(139, 92, 246, 0.3) 100%);
  background-origin: padding-box, border-box;
  background-clip: padding-box, border-box;
  box-shadow:
    0 -2px 12px rgba(14, 165, 233, 0.08),
    0 4px 16px rgba(139, 92, 246, 0.06),
    0 8px 24px rgba(99, 102, 241, 0.04),
    inset 0 -1px 2px rgba(255, 255, 255, 0.9);
  position: relative;
}

/* 頂部分隔線 */
.input-area::before {
  content: '';
  position: absolute;
  top: 0;
  left: 16px;
  right: 16px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(203, 213, 225, 0.5) 20%,
    rgba(148, 163, 184, 0.5) 50%,
    rgba(203, 213, 225, 0.5) 80%,
    transparent 100%
  );
}
</style>
