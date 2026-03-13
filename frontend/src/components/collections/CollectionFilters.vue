<script setup lang="ts">
import type { CollectionListParams } from '@/types/collection'
import { NButton, NInput, NSelect, NSpace } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
const chunkingStrategyOptions = computed(() => [
  { label: t('collections.filters.all'), value: '' },
  { label: t('collections.filters.strategyOptions.qa_multi_representation'), value: 'qa_multi_representation' },
  { label: t('collections.filters.strategyOptions.regulation_hierarchical'), value: 'regulation_hierarchical' },
  { label: t('collections.filters.strategyOptions.regulation_manual_scenario'), value: 'regulation_manual_scenario' },
])

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
          <label class="filter-label">{{ $t('collections.filters.nameLabel') }}</label>
          <NInput
            v-model:value="filters.name"
            :placeholder="$t('collections.filters.namePlaceholder')"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">{{ $t('collections.filters.strategyLabel') }}</label>
          <NSelect
            v-model:value="filters.chunking_strategy"
            :options="chunkingStrategyOptions"
            :placeholder="$t('collections.filters.strategyPlaceholder')"
            clearable
            style="width: 200px"
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
  .filter-item :deep(.n-input) {
    width: 100% !important;
  }

  .filter-actions {
    margin-top: 8px;
    width: 100%;
  }
}
</style>
