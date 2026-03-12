<script setup lang="ts">
import type { RegulationListParams } from '@/types/regulation'
import { NButton, NInput, NSelect, NSpace } from 'naive-ui'
import { ref } from 'vue'

const emit = defineEmits<{
  search: [params: RegulationListParams]
  reset: []
}>()

// 篩選條件
const filters = ref({
  law_name: '' as string,
  category: '' as string,
  status: '' as string,
})

// 法規類別選項
const categoryOptions = [
  { label: '全部', value: '' },
  { label: '憲法', value: '憲法' },
  { label: '法律', value: '法律' },
  { label: '命令', value: '命令' },
  { label: '行政規則', value: '行政規則' },
  { label: '自治法規', value: '自治法規' },
]

// 法規狀態選項
const statusOptions = [
  { label: '全部', value: '' },
  { label: '現行', value: '現行' },
  { label: '廢止', value: '廢止' },
  { label: '停止適用', value: '停止適用' },
  { label: '尚未生效', value: '尚未生效' },
]

// 處理搜尋
function handleSearch() {
  // 移除空值
  const params: RegulationListParams = {}
  if (filters.value.law_name && filters.value.law_name !== '')
    params.law_name = filters.value.law_name
  if (filters.value.category && filters.value.category !== '')
    params.category = filters.value.category
  if (filters.value.status && filters.value.status !== '')
    params.status = filters.value.status

  emit('search', params)
}

// 處理重置
function handleReset() {
  filters.value = {
    law_name: '',
    category: '',
    status: '',
  }
  emit('reset')
}
</script>

<template>
  <div class="filters-container">
    <NSpace vertical :size="16">
      <!-- 第一行：法規名稱 -->
      <NSpace :size="16" align="center">
        <div class="filter-item">
          <label class="filter-label">法規名稱</label>
          <NInput
            v-model:value="filters.law_name"
            placeholder="搜尋法規名稱"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">法規類別</label>
          <NSelect
            v-model:value="filters.category"
            :options="categoryOptions"
            placeholder="選擇法規類別"
            clearable
            style="width: 180px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">法規狀態</label>
          <NSelect
            v-model:value="filters.status"
            :options="statusOptions"
            placeholder="選擇法規狀態"
            clearable
            style="width: 150px"
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
