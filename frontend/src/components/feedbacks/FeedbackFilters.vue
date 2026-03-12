<script setup lang="ts">
import type { FeedbackListParams, FeedbackType } from '@/types/feedback'
import { NButton, NDatePicker, NSelect, NSpace } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { getCollectionList } from '@/api/collections'

const emit = defineEmits<{
  search: [params: FeedbackListParams]
  reset: []
}>()

// 內部表單狀態(與 UI 綁定)
const filters = ref({
  feedback_type: '' as FeedbackType | '',
  is_reviewed: '' as 'true' | 'false' | '',
  dateRange: null as [number, number] | null,
  graph_type: '' as string,
  collection_id: null as number | null,
})

const feedbackTypeOptions = [
  { label: '全部', value: '' },
  { label: '喜歡', value: 'thumbs_up' as FeedbackType },
  { label: '不喜歡', value: 'thumbs_down' as FeedbackType },
]

const reviewStatusOptions = [
  { label: '全部', value: '' },
  { label: '已審查', value: 'true' },
  { label: '未審查', value: 'false' },
]

const graphTypeOptions = [
  { label: '全部', value: '' },
  { label: '基礎對話', value: 'base_graph' },
  { label: 'RAG 對話', value: 'rag_graph' },
  { label: '法規查詢', value: 'regulation_graph' },
]

const collectionOptions = ref<Array<{ label: string, value: number }>>([])

// 載入 Collections 列表
async function loadCollections() {
  try {
    const response = await getCollectionList()
    if (response.items) {
      collectionOptions.value = response.items.map(collection => ({
        label: collection.name,
        value: collection.id,
      }))
    }
  }
  catch (error) {
    console.error('載入知識庫列表失敗:', error)
  }
}

onMounted(() => {
  loadCollections()
})

function handleSearch() {
  const params: FeedbackListParams = {}

  if (filters.value.feedback_type) {
    params.feedback_type = filters.value.feedback_type as FeedbackType
  }

  if (filters.value.is_reviewed) {
    params.is_reviewed = filters.value.is_reviewed === 'true'
  }

  if (filters.value.dateRange) {
    const [start, end] = filters.value.dateRange
    params.start_date = new Date(start).toISOString()
    params.end_date = new Date(end).toISOString()
  }

  if (filters.value.graph_type) {
    params.graph_type = filters.value.graph_type
  }

  if (filters.value.collection_id) {
    params.collection_id = filters.value.collection_id
  }

  emit('search', params)
}

function handleReset() {
  filters.value = {
    feedback_type: '',
    is_reviewed: '',
    dateRange: null,
    graph_type: '',
    collection_id: null,
  }
  emit('reset')
}
</script>

<template>
  <div class="filters-container">
    <NSpace vertical :size="16">
      <NSpace :size="16" align="center">
        <div class="filter-item">
          <label class="filter-label">反饋類型</label>
          <NSelect
            v-model:value="filters.feedback_type"
            :options="feedbackTypeOptions"
            placeholder="選擇反饋類型"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">審查狀態</label>
          <NSelect
            v-model:value="filters.is_reviewed"
            :options="reviewStatusOptions"
            placeholder="選擇審查狀態"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">Agent 類型</label>
          <NSelect
            v-model:value="filters.graph_type"
            :options="graphTypeOptions"
            placeholder="選擇 Agent 類型"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">知識庫</label>
          <NSelect
            v-model:value="filters.collection_id"
            :options="collectionOptions"
            placeholder="選擇知識庫"
            clearable
            filterable
            style="width: 200px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">建立時間</label>
          <NDatePicker
            v-model:value="filters.dateRange"
            type="daterange"
            clearable
            style="width: 280px"
          />
        </div>

        <div class="filter-actions">
          <NSpace :size="12">
            <NButton type="primary" @click="handleSearch">
              搜尋
            </NButton>
            <NButton @click="handleReset">
              重置
            </NButton>
          </NSpace>
        </div>
      </NSpace>
    </NSpace>
  </div>
</template>

<style scoped>
.filters-container {
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.filter-actions {
  margin-top: 24px;
}

@media (max-width: 768px) {
  .filters-container {
    padding: 16px;
  }

  .filters-container :deep(.n-space) {
    flex-wrap: wrap !important;
  }

  .filter-item {
    min-width: 100%;
  }

  .filter-item :deep(.n-select),
  .filter-item :deep(.n-date-picker) {
    width: 100% !important;
  }

  .filter-actions {
    margin-top: 8px;
    width: 100%;
  }
}
</style>
