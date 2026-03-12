<script setup lang="ts">
import type { PaginationMeta } from '@/types/api'
import type { FeedbackListItem, FeedbackListParams } from '@/types/feedback'
import { RefreshOutline as RefreshIcon } from '@vicons/ionicons5'
import { NButton, NIcon } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { getFeedbackList } from '@/api/feedback'
import FeedbackFilters from '@/components/feedbacks/FeedbackFilters.vue'
import FeedbackTable from '@/components/feedbacks/FeedbackTable.vue'
import { message } from '@/utils/message'

// 狀態
const loading = ref(false)
const feedbacks = ref<FeedbackListItem[]>([])
const pagination = ref<PaginationMeta>({
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0,
})

// 篩選條件
const currentFilters = ref<FeedbackListParams>({})

// 載入反饋列表
async function loadFeedbacks() {
  loading.value = true
  try {
    const params: FeedbackListParams = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ...currentFilters.value,
    }

    const response = await getFeedbackList(params)

    feedbacks.value = response.items
    pagination.value = response.pagination
  }
  catch (error: any) {
    console.error('載入反饋列表失敗:', error)
    message.error(error.message || '載入反饋列表失敗')
  }
  finally {
    loading.value = false
  }
}

// 處理搜尋
function handleSearch(filters: FeedbackListParams) {
  currentFilters.value = filters
  pagination.value.page = 1 // 重置頁碼
  loadFeedbacks()
}

// 處理重置
function handleReset() {
  currentFilters.value = {}
  pagination.value.page = 1
  loadFeedbacks()
}

// 處理頁碼變更
function handlePageChange(page: number) {
  pagination.value.page = page
  loadFeedbacks()
}

// 處理每頁數量變更
function handlePageSizeChange(pageSize: number) {
  pagination.value.page_size = pageSize
  pagination.value.page = 1
  loadFeedbacks()
}

// 手動重新整理
async function handleRefresh() {
  await loadFeedbacks()
  message.success('重新整理成功')
}

onMounted(() => {
  loadFeedbacks()
})
</script>

<template>
  <div class="feedback-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          反饋記錄管理
        </h1>
        <p class="page-description">
          查看和管理用戶反饋記錄
        </p>
      </div>
      <div class="header-actions">
        <NButton type="primary" size="large" :loading="loading" @click="handleRefresh">
          <template #icon>
            <NIcon :component="RefreshIcon" />
          </template>
          重新整理
        </NButton>
      </div>
    </div>

    <!-- 篩選器 -->
    <div class="filters-section">
      <FeedbackFilters @search="handleSearch" @reset="handleReset" />
    </div>

    <!-- 列表表格 -->
    <div class="table-section">
      <FeedbackTable
        :data="feedbacks"
        :pagination="pagination"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
.feedback-management {
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e5e7eb;
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.page-description {
  margin: 8px 0 0;
  font-size: 0.9375rem;
  color: #6b7280;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filters-section {
  margin-bottom: 24px;
}

.table-section {
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .feedback-management {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions button {
    flex: 1;
  }
}
</style>
