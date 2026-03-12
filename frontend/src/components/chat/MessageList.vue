<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'
import type { Feedback } from '@/types/feedback'
import { NEmpty, NSpin } from 'naive-ui'
import { onMounted, onUnmounted, watch } from 'vue'
import { useMessageScroll } from '@/composables/useMessageScroll'
import { useChatStore } from '@/stores/chat'
import MessageItem from './MessageItem.vue'

interface Props {
  messages: ChatMessage[]
  loading?: boolean
  streaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  streaming: false,
})

const chatStore = useChatStore()

// 使用自動滾動 composable
const {
  scrollContainer,
  shouldAutoScroll,
  scrollToBottom,
  handleScroll,
  enableAutoScrollAndScroll,
} = useMessageScroll()

// 定期滾動的 interval
let scrollInterval: ReturnType<typeof setInterval> | null = null

// 監聽訊息變化,自動滾動
watch(
  () => props.messages.length,
  async () => {
    await scrollToBottom(true)
  },
)

// 監聽串流狀態,確保串流時保持滾動
watch(
  () => props.streaming,
  async (isStreaming) => {
    if (isStreaming) {
      // 串流開始時,滾動到底部並啟用自動滾動
      await enableAutoScrollAndScroll()

      // 開始定期滾動 (每 200ms 檢查並滾動)
      if (scrollInterval) {
        clearInterval(scrollInterval)
      }
      scrollInterval = setInterval(() => {
        scrollToBottom(false) // 使用非平滑滾動,更即時
      }, 200)
    }
    else {
      // 串流結束,停止定期滾動
      if (scrollInterval) {
        clearInterval(scrollInterval)
        scrollInterval = null
      }
      // 最後滾動一次確保到底
      await scrollToBottom(true)
    }
  },
)

// 組件掛載時滾動到底部
onMounted(async () => {
  await scrollToBottom(false)
})

// 組件卸載時清理 interval
onUnmounted(() => {
  if (scrollInterval) {
    clearInterval(scrollInterval)
    scrollInterval = null
  }
})

// 處理反饋變更
function handleFeedbackChanged(messageId: string, feedback: Feedback) {
  chatStore.updateMessageFeedback(messageId, feedback)
}
</script>

<template>
  <div
    :ref="(el) => { scrollContainer = el as HTMLElement | null }"
    class="message-list-container"
    @scroll="handleScroll"
  >
    <!-- Loading 狀態 -->
    <div v-if="loading && messages.length === 0" class="loading-container">
      <NSpin size="medium">
        <template #description>
          載入訊息中...
        </template>
      </NSpin>
    </div>

    <!-- 訊息列表 -->
    <div v-else-if="messages.length > 0" class="message-list">
      <MessageItem
        v-for="(message, index) in messages"
        :key="message.id"
        :message="message"
        :is-last-message="index === messages.length - 1"
        :is-streaming="streaming"
        @feedback-changed="handleFeedbackChanged"
      />

      <!-- 串流中的載入提示 -->
      <div v-if="streaming" class="streaming-indicator">
        <NSpin size="small" />
        <span class="streaming-text">AI 正在思考...</span>
      </div>
    </div>

    <!-- 空狀態 -->
    <div v-else class="empty-container">
      <NEmpty
        description="尚無訊息"
        size="large"
      />
    </div>

    <!-- 回到底部按鈕 -->
    <Transition name="fade">
      <button
        v-if="!shouldAutoScroll && messages.length > 0"
        class="scroll-to-bottom-btn"
        @click="enableAutoScrollAndScroll"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
        <span>回到底部</span>
      </button>
    </Transition>
  </div>
</template>

<style scoped>
.message-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  position: relative;
  scroll-behavior: smooth;
  background: transparent;
}

/* 自訂滾動條樣式 */
.message-list-container::-webkit-scrollbar {
  width: 8px;
}

.message-list-container::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.message-list-container::-webkit-scrollbar-thumb {
  background: rgba(203, 213, 225, 0.5);
  border-radius: 4px;
  transition: background 0.2s ease;
}

.message-list-container::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.7);
}

/* Loading 狀態 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 300px;
}

/* 訊息列表 */
.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

/* 空狀態 */
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 300px;
}

/* 串流指示器 */
.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f0f9ff 0%, #faf5ff 100%);
  border-radius: 12px;
  max-width: 200px;
  margin-top: 8px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.1);
}

.streaming-text {
  font-size: 0.875rem;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

/* 回到底部按鈕 */
.scroll-to-bottom-btn {
  position: fixed;
  bottom: 120px;
  right: 40px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 20px;
  box-shadow:
    0 4px 12px rgba(14, 165, 233, 0.15),
    0 2px 6px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  transition: all 0.2s ease;
  z-index: 10;
}

.scroll-to-bottom-btn:hover {
  background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow:
    0 8px 20px rgba(14, 165, 233, 0.2),
    0 4px 8px rgba(139, 92, 246, 0.15);
  transform: translateY(-2px);
}

.scroll-to-bottom-btn:active {
  transform: translateY(0);
}

/* 淡入淡出動畫 */
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .message-list-container {
    padding: 12px;
  }

  .scroll-to-bottom-btn {
    bottom: 100px;
    right: 20px;
    padding: 8px 12px;
    font-size: 0.8125rem;
  }
}
</style>
