<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'
import type { Feedback } from '@/types/feedback'
import { computed } from 'vue'
import { useMessageMetadata } from '@/composables/useMessageMetadata'
import MessageAttachments from './message/MessageAttachments.vue'
import MessageContent from './message/MessageContent.vue'
import MessageMetadata from './message/MessageMetadata.vue'
import ToolOutputFiles from './message/ToolOutputFiles.vue'
import MessageFeedback from './MessageFeedback.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  message: ChatMessage
  isLastMessage?: boolean
  isStreaming?: boolean
}

interface Emits {
  (e: 'feedbackChanged', messageId: string, feedback: Feedback): void
}

const props = withDefaults(defineProps<Props>(), {
  isLastMessage: false,
  isStreaming: false,
})
const emit = defineEmits<Emits>()

// 使用 Composable
const {
  hasAttachments,
  hasMetadata,
  hasToolOutputFiles,
  shouldShowFeedback,
} = useMessageMetadata(props.message, props.isLastMessage, props.isStreaming)

// 判斷是否為使用者訊息
const isUser = computed(() => props.message.role === 'user')

// 格式化時間
function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 處理反饋變更
function handleFeedbackChanged(feedback: Feedback) {
  emit('feedbackChanged', props.message.id, feedback)
}
</script>

<template>
  <div
    class="message-item" :class="[isUser ? 'message-user' : 'message-assistant']"
  >
    <!-- 使用者訊息 -->
    <div v-if="isUser" class="message-content user-message">
      <div class="message-header">
        <span class="message-role">{{ t('chat.messages.userRole') }}</span>
        <span class="message-time">{{ formatTime(message.created_at) }}</span>
      </div>

      <!-- 附件顯示 -->
      <MessageAttachments
        v-if="hasAttachments && message.attachments"
        :attachments="message.attachments"
        :message-id="message.id"
      />

      <!-- 訊息文字 -->
      <div v-if="message.content" class="message-text">
        {{ message.content }}
      </div>
    </div>

    <!-- Assistant 訊息 -->
    <div v-else class="message-content assistant-message">
      <div class="message-header">
        <span class="message-role">{{ t('chat.messages.assistantRole') }}</span>
        <span class="message-time">{{ formatTime(message.created_at) }}</span>
      </div>

      <!-- 主要訊息內容 - 使用 Markdown 渲染 -->
      <MessageContent :content="message.content" />

      <!-- 工具產出檔案 -->
      <ToolOutputFiles
        v-if="hasToolOutputFiles && message.metadata?.tool_results"
        :tool-results="message.metadata.tool_results"
      />

      <!-- Metadata 區塊 -->
      <MessageMetadata
        v-if="hasMetadata"
        :message="message"
      />

      <!-- 反饋按鈕 - 放在最底部左側 -->
      <div v-if="shouldShowFeedback" class="message-feedback-container">
        <MessageFeedback
          :message-id="message.id"
          :message-content="message.content"
          :existing-feedback="message.user_feedback"
          @feedback-changed="handleFeedbackChanged"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-item {
  width: 100%;
  padding: 12px 0;
}

.message-content {
  max-width: 800px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

/* 使用者訊息 - 右對齊 */
.message-user {
  display: flex;
  justify-content: flex-end;
}

.user-message {
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  color: white;
  margin-left: auto;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25);
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.85);
}

/* Assistant 訊息 - 左對齊 */
.message-assistant {
  display: flex;
  justify-content: flex-start;
}

.assistant-message {
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border: 1px solid #e5e7eb;
  margin-right: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 訊息頭部 */
.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.875rem;
}

.message-role {
  font-weight: 600;
}

.message-time {
  font-size: 0.75rem;
  color: #6b7280;
}

/* 訊息文字 */
.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.9375rem;
}

/* 反饋按鈕容器 - 靠左對齊 */
.message-feedback-container {
  display: flex;
  justify-content: flex-start;
  margin-top: 8px;
  padding-top: 4px;
}

@media (max-width: 768px) {
  .message-content {
    max-width: 100%;
    padding: 12px;
  }

  .message-text {
    font-size: 0.875rem;
  }
}
</style>
