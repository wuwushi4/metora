<script setup lang="ts">
import type { FeedbackDetail } from '@/types/feedback'
import { ArrowBackOutline as BackIcon, DocumentTextOutline } from '@vicons/ionicons5'
import {
  NButton,
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NEmpty,
  NIcon,
  NImage,
  NSpace,
  NSpin,
  NTag,
} from 'naive-ui'
import { useBreakpoints } from '@vueuse/core'
import { computed, onMounted, ref } from 'vue'
import MarkdownRender from 'vue-renderer-markdown'
import { useRoute, useRouter } from 'vue-router'
import { getAttachmentUrl } from '@/api/chat'
import { getFeedbackDetail } from '@/api/feedback'
import ExpertReviewForm from '@/components/feedbacks/ExpertReviewForm.vue'
import RetrievalResultsCard from '@/components/feedbacks/RetrievalResultsCard.vue'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/date'
import { message } from '@/utils/message'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const feedback = ref<FeedbackDetail | null>(null)
const loading = ref(false)
const loadError = ref<string | null>(null)

const breakpoints = useBreakpoints({ mobile: 768 })
const descriptionColumn = computed(() => breakpoints.smaller('mobile').value ? 1 : 2)

const feedbackId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' ? id : null
})
const isAdmin = computed(() => authStore.user?.roles?.includes('admin') ?? false)
const isDisliked = computed(() => feedback.value?.feedback_type === 'thumbs_down')
const canReview = computed(
  () => isAdmin.value && isDisliked.value && !feedback.value?.expert_review,
)
const hasRetrievalResults = computed(
  () =>
    feedback.value?.message.extra_data?.retrieval_results
    && feedback.value.message.extra_data.retrieval_results.length > 0,
)
const hasUserAttachments = computed(
  () =>
    feedback.value?.user_message?.attachments
    && feedback.value.user_message.attachments.length > 0,
)
const isInterrupted = computed(
  () => feedback.value?.message.extra_data?.interrupted === true,
)

// Agent 類型標籤映射
function getGraphTypeLabel(graphType: string): string {
  const key = `feedbacks.filters.graphTypes.${graphType}`
  const translated = t(key)
  return translated !== key ? translated : graphType
}

async function loadDetail() {
  const id = feedbackId.value
  if (!id) {
    loadError.value = t('feedbacks.detail.loadFailed')
    message.error(loadError.value)
    return
  }

  loading.value = true
  loadError.value = null

  try {
    feedback.value = await getFeedbackDetail(id)
  }
  catch (error: any) {
    console.error('載入反饋詳情失敗:', error)
    const errorMsg = error.message || t('feedbacks.detail.loadFailed')
    loadError.value = errorMsg
    message.error(errorMsg)
  }
  finally {
    loading.value = false
  }
}

function handleBack() {
  router.push('/feedbacks')
}

async function handleReviewSubmitted() {
  message.success(t('feedbacks.expertReview.success'))
  await loadDetail()
}

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div class="feedback-detail">
    <!-- 返回按鈕 -->
    <div class="page-header">
      <NButton @click="handleBack">
        <template #icon>
          <NIcon :component="BackIcon" />
        </template>
        {{ t('common.actions.backToList') }}
      </NButton>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="loading-container">
      <NSpin size="large" />
    </div>

    <!-- 載入錯誤 -->
    <NEmpty
      v-else-if="loadError || !feedback"
      :description="t('feedbacks.detail.loadError')"
      :show-description="true"
    >
      <template #extra>
        <NButton @click="loadDetail">
          {{ t('common.actions.retry') }}
        </NButton>
      </template>
    </NEmpty>

    <!-- 內容 -->
    <div v-else class="content-container">
      <!-- 反饋資訊卡片 -->
      <NCard :title="t('feedbacks.detail.feedbackInfo')">
        <NDescriptions :column="descriptionColumn" label-placement="left" bordered>
          <NDescriptionsItem :label="t('feedbacks.detail.feedbackId')">
            {{ feedback.id }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.messageId')">
            {{ feedback.message_id }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.agentType')">
            <NTag type="info" size="small">
              {{ getGraphTypeLabel(feedback.graph_type) }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.collection')">
            <NSpace v-if="feedback.collection_names && feedback.collection_names.length > 0" :size="8">
              <NTag
                v-for="name in feedback.collection_names"
                :key="name"
                type="success"
                size="small"
              >
                {{ name }}
              </NTag>
            </NSpace>
            <span v-else>-</span>
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.user')">
            {{ feedback.user?.full_name || feedback.user?.username || t('feedbacks.detail.unknownUser') }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.feedbackType')">
            <NTag
              :type="feedback.feedback_type === 'thumbs_up' ? 'success' : 'error'"
              size="small"
            >
              {{ feedback.feedback_type === 'thumbs_up' ? t('feedbacks.detail.like') : t('feedbacks.detail.dislike') }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem
            v-if="feedback.issue_tags && feedback.issue_tags.length > 0"
            :label="t('feedbacks.detail.issueLabels')"
            :span="2"
          >
            <NSpace :size="8">
              <NTag
                v-for="tag in feedback.issue_tags"
                :key="tag"
                type="warning"
                size="small"
              >
                {{ tag }}
              </NTag>
            </NSpace>
          </NDescriptionsItem>
          <NDescriptionsItem v-if="feedback.comment" :label="t('feedbacks.detail.userComment')" :span="2">
            {{ feedback.comment }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('common.fields.createdAt')" :span="2">
            {{ formatDateTime(feedback.created_at) }}
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>

      <!-- 對話內容卡片 -->
      <NCard :title="t('feedbacks.detail.conversationContent')" class="mt-4">
        <div class="conversation">
          <div class="user-question">
            <h3 class="section-title">
              {{ t('feedbacks.detail.userQuestion') }}
            </h3>

            <!-- 附件顯示區 -->
            <div v-if="hasUserAttachments" class="user-attachments">
              <div class="attachments-grid">
                <div
                  v-for="attachment in feedback.user_message!.attachments"
                  :key="attachment.id"
                  class="attachment-item"
                >
                  <!-- 圖片附件 -->
                  <NImage
                    v-if="attachment.attachment_type === 'image'"
                    :src="getAttachmentUrl(feedback.user_message!.id, attachment.id)"
                    :alt="attachment.original_filename"
                    object-fit="cover"
                    class="attachment-image"
                    :preview-src="getAttachmentUrl(feedback.user_message!.id, attachment.id)"
                  />

                  <!-- PDF 頁面附件 -->
                  <div
                    v-else-if="attachment.attachment_type === 'pdf_page'"
                    class="pdf-attachment"
                  >
                    <NImage
                      :src="getAttachmentUrl(feedback.user_message!.id, attachment.id)"
                      :alt="`${attachment.original_filename} - p.${attachment.extra_data?.page_number}`"
                      object-fit="cover"
                      class="attachment-image"
                      :preview-src="getAttachmentUrl(feedback.user_message!.id, attachment.id)"
                    />
                    <!-- 頁碼標籤 -->
                    <div class="pdf-page-label">
                      <NIcon :size="14" color="white">
                        <DocumentTextOutline />
                      </NIcon>
                      <span class="page-info">
                        第 {{ attachment.extra_data?.page_number }}/{{ attachment.extra_data?.total_pages }} 頁
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 文字內容 -->
            <div class="question-content">
              {{ feedback.user_question || t('feedbacks.detail.noQuestion') }}
            </div>
          </div>

          <div class="assistant-response">
            <div class="section-header">
              <h3 class="section-title">
                {{ t('feedbacks.detail.aiReply') }}
              </h3>
              <NTag v-if="isInterrupted" type="warning" size="small" :bordered="false">
                <template #icon>
                  <NIcon>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                    </svg>
                  </NIcon>
                </template>
                {{ t('feedbacks.detail.userInterrupted') }}
              </NTag>
            </div>
            <div class="response-content markdown-content">
              <MarkdownRender :content="feedback.message.content" />
            </div>
          </div>
        </div>
      </NCard>

      <!-- RAG 檢索結果 -->
      <RetrievalResultsCard
        v-if="hasRetrievalResults"
        :results="feedback.message.extra_data.retrieval_results"
        class="mt-4"
      />

      <!-- 專家審查表單 -->
      <ExpertReviewForm
        v-if="canReview"
        :feedback-id="feedback.id"
        class="mt-4"
        @submit="handleReviewSubmitted"
      />

      <!-- 已審查資訊 -->
      <NCard v-if="feedback.expert_review" :title="t('feedbacks.detail.expertReview')" class="mt-4">
        <NDescriptions :column="1" label-placement="left" bordered>
          <NDescriptionsItem :label="t('feedbacks.detail.reviewer')">
            {{
              feedback.expert_review.reviewer?.full_name
                || feedback.expert_review.reviewer?.username
                || t('feedbacks.detail.unknown')
            }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.expertOpinion')">
            <div class="expert-opinion">
              {{ feedback.expert_review.expert_opinion }}
            </div>
          </NDescriptionsItem>
          <NDescriptionsItem
            v-if="feedback.expert_review.suggested_response"
            :label="t('feedbacks.detail.suggestedReply')"
          >
            <div class="suggested-response">
              {{ feedback.expert_review.suggested_response }}
            </div>
          </NDescriptionsItem>
          <NDescriptionsItem :label="t('feedbacks.detail.reviewTime')">
            {{ formatDateTime(feedback.expert_review.created_at) }}
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.feedback-detail {
  padding: 20px;
}

.page-header {
  margin-bottom: 16px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.conversation {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--n-title-text-color);
}

.question-content,
.response-content {
  padding: 16px;
  background-color: var(--n-color);
  border-radius: 8px;
  line-height: 1.6;
}

.expert-opinion,
.suggested-response {
  white-space: pre-wrap;
  line-height: 1.6;
}

/* Markdown 內容樣式 */
.markdown-content {
  line-height: 1.7;
  word-wrap: break-word;
}

/* Markdown 渲染器的深層樣式覆寫 */
.markdown-content :deep(.markdown-body) {
  font-size: 0.9375rem;
  color: inherit;
  background: transparent;
}

/* 段落 */
.markdown-content :deep(p) {
  margin: 0.75em 0;
  line-height: 1.7;
}

.markdown-content :deep(p:first-child) {
  margin-top: 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

/* 標題 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin: 1.2em 0 0.6em;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 1.75em;
}
.markdown-content :deep(h2) {
  font-size: 1.5em;
}
.markdown-content :deep(h3) {
  font-size: 1.25em;
}
.markdown-content :deep(h4) {
  font-size: 1.1em;
}
.markdown-content :deep(h5) {
  font-size: 1em;
}
.markdown-content :deep(h6) {
  font-size: 0.95em;
}

/* 清單 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.75em 0;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin: 0.3em 0;
  line-height: 1.6;
}

.markdown-content :deep(ul ul),
.markdown-content :deep(ol ul),
.markdown-content :deep(ul ol),
.markdown-content :deep(ol ol) {
  margin: 0.25em 0;
}

/* 程式碼區塊 (pre + code) */
.markdown-content :deep(pre) {
  margin: 1em 0;
  padding: 1.25em;
  border-radius: 8px;
  overflow-x: auto;
  background: #282c34 !important; /* VS Code Dark+ 主題背景 */
  border: 1px solid #3e4451;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.markdown-content :deep(pre code) {
  background: transparent !important;
  padding: 0 !important;
  border-radius: 0;
  border: none !important;
  font-size: 0.875em;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  /* VS Code Dark+ 主題預設文字顏色 - 淺灰白色 */
  color: #abb2bf !important;
}

/* 行內程式碼 (僅 code 不在 pre 內) */
.markdown-content :deep(:not(pre) > code) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875em;
  padding: 0.2em 0.4em;
  background: #f3f4f6;
  border-radius: 4px;
  color: #e11d48;
  border: 1px solid #e5e7eb;
  font-weight: 500;
}

/* 引用區塊 */
.markdown-content :deep(blockquote) {
  margin: 1em 0;
  padding: 0.5em 0 0.5em 1em;
  border-left: 4px solid #8b5cf6;
  background: #f9fafb;
  color: #6b7280;
  border-radius: 0 4px 4px 0;
}

.markdown-content :deep(blockquote p) {
  margin: 0.5em 0;
}

/* 表格 */
.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5em 0.75em;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.markdown-content :deep(tr:nth-child(even)) {
  background: #fafafa;
}

/* 水平分隔線 */
.markdown-content :deep(hr) {
  margin: 1.5em 0;
  border: none;
  border-top: 2px solid #e5e7eb;
}

/* 連結 */
.markdown-content :deep(a) {
  color: #3b82f6;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s;
}

.markdown-content :deep(a:hover) {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

/* 粗體 */
.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1f2937;
}

/* 斜體 */
.markdown-content :deep(em) {
  font-style: italic;
  color: #4b5563;
}

/* 刪除線 */
.markdown-content :deep(del) {
  text-decoration: line-through;
  color: #9ca3af;
}

/* 任務清單 */
.markdown-content :deep(input[type='checkbox']) {
  margin-right: 0.5em;
}

/* 圖片 */
.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 0.75em 0;
}

/* 附件區域樣式 */
.user-attachments {
  margin-bottom: 12px;
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.attachment-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(150, 150, 150, 0.05);
  aspect-ratio: 1;
  border: 1px solid var(--n-border-color);
}

.attachment-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.attachment-image:hover {
  transform: scale(1.05);
}

/* PDF 附件樣式 */
.pdf-attachment {
  position: relative;
  width: 100%;
  height: 100%;
}

.pdf-page-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.page-info {
  font-size: 11px;
  font-weight: 600;
  color: white;
  letter-spacing: 0.3px;
}

@media (max-width: 768px) {
  .feedback-detail {
    padding: 16px;
  }

  .question-content,
  .response-content {
    padding: 12px;
  }

  .attachments-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }

  .markdown-content :deep(pre) {
    padding: 0.75em;
    font-size: 0.8125rem;
  }

  .markdown-content :deep(table) {
    display: block;
    overflow-x: auto;
  }
}
</style>
