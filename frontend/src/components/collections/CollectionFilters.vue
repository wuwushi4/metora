<script setup lang="ts">
import type { CollectionListParams } from '@/types/collection'
import { NButton, NInput, NSelect, NSpace } from 'naive-ui'
import { ref } from 'vue'

const emit = defineEmits<{
  search: [params: CollectionListParams]
  reset: []
}>()

// 篩選條件
const filters = ref({
  name: '' as string,
  chunking_strategy: '' as string,
})

// 分塊策略選項
const chunkingStrategyOptions = [
  { label: '全部', value: '' },
  { label: 'QA 多重表徵', value: 'qa_multi_representation' },
  { label: '法規階層式', value: 'regulation_hierarchical' },
  // { label: '法規情境增強', value: 'regulation_context_enriched' },
  { label: '法規手動情境', value: 'regulation_manual_scenario' },
]

// 處理搜尋
function handleSearch() {
  // 移除空值
  const params: CollectionListParams = {}
  if (filters.value.name && filters.value.name !== '')
    params.name = filters.value.name
  if (filters.value.chunking_strategy && filters.value.chunking_strategy !== '')
    params.chunking_strategy = filters.value.chunking_strategy

  emit('search', params)
}

// 處理重置
function handleReset() {
  filters.value = {
    name: '',
    chunking_strategy: '',
  }
  emit('reset')
}
</script>

<template>
  <div class="filters-container">
    <NSpace vertical :size="16">
      <!-- 第一行：Collection 名稱和分塊策略 -->
      <NSpace :size="16" align="center">
        <div class="filter-item">
          <label class="filter-label">Collection 名稱</label>
          <NInput
            v-model:value="filters.name"
            placeholder="搜尋 Collection 名稱"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">分塊策略</label>
          <NSelect
            v-model:value="filters.chunking_strategy"
            :options="chunkingStrategyOptions"
            placeholder="選擇分塊策略"
            clearable
            style="width: 200px"
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
  .filter-item :deep(.n-input) {
    width: 100% !important;
  }

  .filter-actions {
    margin-top: 8px;
    width: 100%;
  }
}
</style>
