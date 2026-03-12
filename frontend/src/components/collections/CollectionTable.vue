<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import type { PaginationMeta } from '@/types/api'
import type { Collection } from '@/types/collection'
import {
  NButton,
  NDataTable,
  NPagination,
  NPopconfirm,
  NSpace,
  NTag,
} from 'naive-ui'
import { h } from 'vue'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/utils/date'

interface Props {
  data: Collection[]
  pagination: PaginationMeta
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
  'edit': [collection: Collection]
  'delete': [collectionId: number]
}>()

const router = useRouter()

// 處理查看詳情
function handleView(collection: Collection) {
  router.push(`/collections/${collection.id}`)
}

// 處理編輯
function handleEdit(collection: Collection) {
  emit('edit', collection)
}

// 處理刪除
function handleDelete(collection: Collection) {
  emit('delete', collection.id)
}

// 分塊策略顯示名稱映射
const chunkingStrategyMap: Record<string, { label: string, type: 'info' | 'success' | 'warning' }> = {
  qa_multi_representation: { label: 'QA 多重表徵', type: 'info' },
  regulation_hierarchical: { label: '法規-階層式', type: 'success' },
  // regulation_context_enriched: { label: '法規情境增強', type: 'warning' },
  regulation_manual_scenario: { label: '法規-情境描述', type: 'success' },
}

// 表格欄位定義
const columns: DataTableColumns<Collection> = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: 'Collection 名稱',
    key: 'name',
    minWidth: 150,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: '描述',
    key: 'description',
    minWidth: 200,
    ellipsis: {
      tooltip: true,
    },
    render: (row) => {
      return row.description || '-'
    },
  },
  {
    title: '分塊策略',
    key: 'chunking_strategy',
    width: 140,
    align: 'center',
    render: (row) => {
      const strategy = chunkingStrategyMap[row.chunking_strategy] || {
        label: row.chunking_strategy,
        type: 'info' as const,
      }
      return h(
        NTag,
        {
          size: 'small',
          type: strategy.type,
        },
        { default: () => strategy.label },
      )
    },
  },
  {
    title: 'Dataset 數量',
    key: 'dataset_count',
    width: 120,
    align: 'center',
    render: (row) => {
      return row.dataset_count || 0
    },
  },
  {
    title: '建立時間',
    key: 'created_at',
    width: 180,
    render: (row) => {
      return formatDateTime(row.created_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    fixed: 'right' as const,
    render: (row) => {
      return h(
        NSpace,
        { size: 8 },
        {
          default: () => [
            h(
              NButton,
              {
                size: 'small',
                type: 'info',
                quaternary: true,
                onClick: () => handleView(row),
              },
              { default: () => '查看' },
            ),
            h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                quaternary: true,
                onClick: () => handleEdit(row),
              },
              { default: () => '編輯' },
            ),
            h(
              NPopconfirm,
              {
                onPositiveClick: () => handleDelete(row),
              },
              {
                trigger: () =>
                  h(
                    NButton,
                    {
                      size: 'small',
                      type: 'error',
                      quaternary: true,
                    },
                    { default: () => '刪除' },
                  ),
                default: () => '確定要刪除這個 Collection 嗎？此操作將同時刪除所有關聯的 Dataset。',
              },
            ),
          ],
        },
      )
    },
  },
]

// 處理頁碼變更
function handlePageChange(page: number) {
  emit('update:page', page)
}

// 處理每頁數量變更
function handlePageSizeChange(pageSize: number) {
  emit('update:pageSize', pageSize)
}
</script>

<template>
  <div class="table-container">
    <!-- 表格 -->
    <NDataTable
      :columns="columns"
      :data="data"
      :loading="loading"
      :scroll-x="1200"
      :single-line="false"
      size="medium"
      striped
    />

    <!-- 分頁 -->
    <div class="pagination-container">
      <NPagination
        :page="pagination.page"
        :page-size="pagination.page_size"
        :item-count="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        show-size-picker
        show-quick-jumper
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      >
        <template #prefix="{ itemCount }">
          共 {{ itemCount }} 筆
        </template>
      </NPagination>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.pagination-container {
  padding: 20px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #e5e7eb;
}

/* 確保表格內容不會溢出 */
:deep(.n-data-table) {
  font-size: 0.875rem;
}

:deep(.n-data-table-td) {
  padding: 12px 16px;
}

:deep(.n-data-table-th) {
  padding: 12px 16px;
  background: #f9fafb;
  font-weight: 600;
}
</style>
