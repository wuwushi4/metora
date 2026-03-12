<script setup lang="ts">
import type { Feedback, FeedbackType } from '@/types/feedback'
import {
  CopyOutline as CopyIcon,
  ThumbsDownOutline as ThumbsDownIcon,
  ThumbsUpOutline as ThumbsUpIcon,
} from '@vicons/ionicons5'
import { NButton, NCheckbox, NCheckboxGroup, NIcon, NInput, NModal, NSpace } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { getIssueTags, submitFeedback } from '@/api/feedback'
import { message } from '@/utils/message'

/**
 * Props
 */
interface Props {
  messageId: string
  messageContent: string
  existingFeedback?: Feedback
}

const props = withDefaults(defineProps<Props>(), {
  existingFeedback: undefined,
})

const emit = defineEmits<Emits>()

/**
 * Emits
 */
interface Emits {
  (e: 'feedbackChanged', feedback: Feedback): void
}

/**
 * 狀態
 */
const currentFeedback = ref<Feedback | undefined>(props.existingFeedback)
const isSubmitting = ref(false)

// 負面反饋表單狀態
const showNegativeModal = ref(false)
const selectedIssueTags = ref<string[]>([])
const comment = ref('')
const availableTags = ref<string[]>([])

/**
 * 計算屬性
 */
const isLiked = computed(() => currentFeedback.value?.feedback_type === 'thumbs_up')
const isDisliked = computed(() => currentFeedback.value?.feedback_type === 'thumbs_down')

/**
 * 載入問題標籤列表
 */
onMounted(async () => {
  try {
    const response = await getIssueTags()
    availableTags.value = response.tags
  }
  catch (error) {
    console.error('載入問題標籤失敗:', error)
    availableTags.value = [
      '回答不準確',
      '內容太簡短',
      '格式錯誤',
      '檢索結果不相關',
      '語氣不恰當',
    ]
  }
})

/**
 * 處理「讚」點擊
 */
async function handleLike() {
  if (isSubmitting.value)
    return

  // 如果已經是讚,則不處理
  if (isLiked.value)
    return

  await submitFeedbackData('thumbs_up', [], undefined)
}

/**
 * 處理「踩」點擊
 */
function handleDislike() {
  if (isSubmitting.value)
    return

  // 如果已經是踩,則不處理
  if (isDisliked.value)
    return

  // 顯示負面反饋表單
  selectedIssueTags.value = []
  comment.value = ''
  showNegativeModal.value = true
}

/**
 * 提交負面反饋表單
 */
async function handleSubmitNegativeFeedback() {
  await submitFeedbackData('thumbs_down', selectedIssueTags.value, comment.value)
  showNegativeModal.value = false
}

/**
 * 提交反饋資料
 */
async function submitFeedbackData(
  feedbackType: FeedbackType,
  issueTags?: string[],
  userComment?: string,
) {
  isSubmitting.value = true

  try {
    const response = await submitFeedback({
      message_id: props.messageId,
      feedback_type: feedbackType,
      issue_tags: issueTags,
      comment: userComment,
    })

    // 更新本地狀態
    currentFeedback.value = response.data

    // 通知父組件
    if (response.data) {
      emit('feedbackChanged', response.data)
    }

    // 顯示成功訊息
    message.success('感謝你的回饋!', { duration: 2000 })
  }
  catch (error: any) {
    console.error('提交反饋失敗:', error)
    message.error(error.response?.data?.message || '提交反饋失敗')
  }
  finally {
    isSubmitting.value = false
  }
}

/**
 * 關閉負面反饋表單
 */
function handleCloseModal() {
  showNegativeModal.value = false
  selectedIssueTags.value = []
  comment.value = ''
}

/**
 * 複製訊息內容
 */
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.messageContent)
    message.success('已複製到剪貼簿', { duration: 2000 })
  }
  catch (error) {
    console.error('複製失敗:', error)
    message.error('複製失敗，請手動複製')
  }
}
</script>

<template>
  <div class="message-feedback">
    <!-- 反饋按鈕 -->
    <div class="feedback-buttons">
      <!-- 複製按鈕 -->
      <button
        class="feedback-btn feedback-btn-copy"
        title="複製"
        @click="handleCopy"
      >
        <NIcon :size="18" :component="CopyIcon" />
      </button>

      <!-- 讚按鈕 -->
      <button
        class="feedback-btn feedback-btn-like" :class="[{ 'is-active': isLiked }]"
        :disabled="isSubmitting"
        title="有幫助"
        @click="handleLike"
      >
        <NIcon :size="18" :component="ThumbsUpIcon" />
      </button>

      <!-- 踩按鈕 -->
      <button
        class="feedback-btn feedback-btn-dislike" :class="[{ 'is-active': isDisliked }]"
        :disabled="isSubmitting"
        title="沒有幫助"
        @click="handleDislike"
      >
        <NIcon :size="18" :component="ThumbsDownIcon" />
      </button>
    </div>

    <!-- 負面反饋表單 Modal -->
    <NModal
      v-model:show="showNegativeModal"
      preset="card"
      title="告訴我們更多想法"
      :style="{ maxWidth: '500px' }"
      :closable="true"
      :mask-closable="true"
      @after-leave="handleCloseModal"
    >
      <NSpace vertical :size="16">
        <!-- 問題標籤 -->
        <div>
          <div class="form-label">
            問題類型（可多選）
          </div>
          <NCheckboxGroup v-model:value="selectedIssueTags">
            <NSpace vertical :size="8">
              <NCheckbox
                v-for="tag in availableTags"
                :key="tag"
                :value="tag"
                :label="tag"
              />
            </NSpace>
          </NCheckboxGroup>
        </div>

        <!-- 評論輸入框 -->
        <div>
          <div class="form-label">
            補充說明（選填）
          </div>
          <NInput
            v-model:value="comment"
            type="textarea"
            placeholder="請描述具體問題或建議..."
            :rows="4"
            :maxlength="500"
            show-count
          />
        </div>
      </NSpace>

      <template #footer>
        <div class="modal-footer">
          <NButton @click="handleCloseModal">
            取消
          </NButton>
          <NButton
            type="primary"
            :loading="isSubmitting"
            :disabled="isSubmitting"
            @click="handleSubmitNegativeFeedback"
          >
            送出
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.message-feedback {
  display: inline-flex;
  align-items: center;
}

.feedback-buttons {
  display: flex;
  gap: 4px;
}

/* 反饋按鈕基礎樣式 */
.feedback-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  color: #9ca3af;
}

.feedback-btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.feedback-btn:not(:disabled):hover {
  border-color: #d1d5db;
  background: #f9fafb;
  transform: scale(1.05);
}

.feedback-btn:not(:disabled):active {
  transform: scale(0.95);
}

/* 讚按鈕 */
.feedback-btn-like:not(:disabled):hover {
  color: #3b82f6;
  border-color: #3b82f6;
  background: #eff6ff;
}

.feedback-btn-like.is-active {
  color: #ffffff;
  background: #3b82f6;
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.25);
}

.feedback-btn-like.is-active:hover {
  background: #2563eb;
  border-color: #2563eb;
}

/* 踩按鈕 */
.feedback-btn-dislike:not(:disabled):hover {
  color: #ef4444;
  border-color: #ef4444;
  background: #fef2f2;
}

.feedback-btn-dislike.is-active {
  color: #ffffff;
  background: #ef4444;
  border-color: #ef4444;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.25);
}

.feedback-btn-dislike.is-active:hover {
  background: #dc2626;
  border-color: #dc2626;
}

/* 複製按鈕 */
.feedback-btn-copy:hover {
  color: #6b7280;
  border-color: #6b7280;
  background: #f9fafb;
}

/* Modal 表單樣式 */
.form-label {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--n-text-color);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
