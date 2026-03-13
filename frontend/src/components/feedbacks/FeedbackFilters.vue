<script setup lang="ts">
import type { FeedbackListParams, FeedbackType } from '@/types/feedback'
import { NButton, NDatePicker, NSelect, NSpace } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCollectionList } from '@/api/collections'

const emit = defineEmits<{
  search: [params: FeedbackListParams]
  reset: []
}>()

const { t } = useI18n()

// 內部表單狀態(與 UI 綁定)
const filters = ref({
  feedback_type: '' as FeedbackType | '',
  is_reviewed: '' as 'true' | 'false' | '',
  dateRange: null as [number, number] | null,
  graph_type: '' as string,
  collection_id: null as number | null,
})

const feedbackTypeOptions = computed(() => [
  { label: t('feedbacks.filters.all'), value: '' },
  { label: t('feedbacks.filters.like'), value: 'thumbs_up' as FeedbackType },
  { label: t('feedbacks.filters.dislike'), value: 'thumbs_down' as FeedbackType },
])

const reviewStatusOptions = computed(() => [
  { label: t('feedbacks.filters.all'), value: '' },
  { label: t('feedbacks.filters.reviewed'), value: 'true' },
  { label: t('feedbacks.filters.notReviewed'), value: 'false' },
])

const graphTypeOptions = computed(() => [
  { label: t('feedbacks.filters.all'), value: '' },
  { label: t('feedbacks.filters.graphTypes.base_graph'), value: 'base_graph' },
  { label: t('feedbacks.filters.graphTypes.rag_graph'), value: 'rag_graph' },
  { label: t('feedbacks.filters.graphTypes.regulation_graph'), value: 'regulation_graph' },
])

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
          <label class="filter-label">{{ $t('feedbacks.filters.feedbackTypeLabel') }}</label>
          <NSelect
            v-model:value="filters.feedback_type"
            :options="feedbackTypeOptions"
            :placeholder="$t('feedbacks.filters.feedbackTypePlaceholder')"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">{{ $t('feedbacks.filters.reviewStatusLabel') }}</label>
          <NSelect
            v-model:value="filters.is_reviewed"
            :options="reviewStatusOptions"
            :placeholder="$t('feedbacks.filters.reviewStatusPlaceholder')"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">{{ $t('feedbacks.filters.agentTypeLabel') }}</label>
          <NSelect
            v-model:value="filters.graph_type"
            :options="graphTypeOptions"
            :placeholder="$t('feedbacks.filters.agentTypePlaceholder')"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">{{ $t('feedbacks.filters.collectionLabel') }}</label>
          <NSelect
            v-model:value="filters.collection_id"
            :options="collectionOptions"
            :placeholder="$t('feedbacks.filters.collectionPlaceholder')"
            clearable
            filterable
            style="width: 200px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">{{ $t('feedbacks.filters.dateLabel') }}</label>
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
              {{ $t('common.actions.search') }}
            </NButton>
            <NButton @click="handleReset">
              {{ $t('common.actions.reset') }}
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
