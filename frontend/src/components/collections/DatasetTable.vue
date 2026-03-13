<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import type { PaginationMeta } from '@/types/api'
import type { Dataset } from '@/types/dataset'
import {
  NBadge,
  NButton,
  NDataTable,
  NPagination,
  NPopconfirm,
  NSpace,
  NTooltip,
} from 'naive-ui'
import { h } from 'vue'
import { useI18n } from 'vue-i18n'

interface Props {
  data: Dataset[]
  pagination: PaginationMeta
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
  'delete': [datasetId: number]
}>()

const { t } = useI18n()

// 處理刪除
function handleDelete(dataset: Dataset) {
  emit('delete', dataset.id)
}

// 格式化檔案大小
function formatFileSize(bytes: number): string {
  if (bytes === 0)
    return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`
}

// 表格欄位定義
const columns: DataTableColumns<Dataset> = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: t('collections.dataset.originalFilename'),
    key: 'original_filename',
    minWidth: 200,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('collections.dataset.fileType'),
    key: 'file_type',
    width: 120,
    align: 'center',
  },
  {
    title: t('collections.dataset.fileSize'),
    key: 'file_size',
    width: 120,
    align: 'center',
    render: (row) => {
      return formatFileSize(row.file_size)
    },
  },
  {
    title: t('collections.dataset.chunkCount'),
    key: 'chunk_count',
    width: 100,
    align: 'center',
    render: (row) => {
      return row.chunk_count || 0
    },
  },
  {
    title: t('collections.dataset.vectorStatus'),
    key: 'vectorized',
    width: 140,
    align: 'center',
    render: (row) => {
      // 情況 1: 向量化失敗（有錯誤訊息）
      if (row.vectorization_error) {
        return h(
          NTooltip,
          {},
          {
            trigger: () => h(
              NBadge,
              { dot: true, type: 'error' },
              { default: () => t('collections.dataset.statusFailed') },
            ),
            default: () => row.vectorization_error,
          },
        )
      }
      // 情況 2: 向量化完成
      else if (row.vectorized) {
        return h(
          NBadge,
          { dot: true, type: 'success' },
          { default: () => t('collections.dataset.statusCompleted') },
        )
      }
      // 情況 3: 處理中
      else {
        return h(
          NBadge,
          { dot: true, type: 'warning', processing: true },
          { default: () => t('collections.dataset.statusProcessing') },
        )
      }
    },
  },
  {
    title: t('common.fields.createdAt'),
    key: 'created_at',
    width: 180,
    render: (row) => {
      return new Date(row.created_at).toLocaleString('zh-TW')
    },
  },
  {
    title: t('common.fields.actions'),
    key: 'actions',
    width: 120,
    fixed: 'right' as const,
    render: (row) => {
      return h(
        NSpace,
        { size: 8 },
        {
          default: () => [
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
                    { default: () => t('common.actions.delete') },
                  ),
                default: () => t('collections.dataset.uploadModal.deleteConfirm'),
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
          {{ $t('collections.table.totalItems', { count: itemCount }) }}
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
