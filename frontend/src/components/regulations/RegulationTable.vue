<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import type { PaginationMeta } from '@/types/api'
import type { Regulation } from '@/types/regulation'
import {
  NButton,
  NDataTable,
  NPagination,
  NPopconfirm,
  NSpace,
  NTag,
} from 'naive-ui'
import { h } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/utils/date'

interface Props {
  data: Regulation[]
  pagination: PaginationMeta
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
  'delete': [regulationId: number]
  'export': [regulation: Regulation]
}>()

const { t } = useI18n()
const router = useRouter()

// 處理查看詳情
function handleView(regulation: Regulation) {
  router.push(`/regulations/${regulation.id}`)
}

// 處理刪除
function handleDelete(regulation: Regulation) {
  emit('delete', regulation.id)
}

// 處理導出
function handleExport(regulation: Regulation) {
  emit('export', regulation)
}

// 法規狀態映射
const statusMap: Record<string, { label: string, type: 'success' | 'warning' | 'error' | 'info' }> = {
  現行: { label: t('regulations.filters.statuses.active'), type: 'success' },
  廢止: { label: t('regulations.filters.statuses.abolished'), type: 'error' },
  停止適用: { label: t('regulations.filters.statuses.suspended'), type: 'warning' },
  尚未生效: { label: t('regulations.filters.statuses.notEffective'), type: 'info' },
}

// 表格欄位定義
const columns: DataTableColumns<Regulation> = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: t('regulations.table.lawCode'),
    key: 'law_code',
    width: 120,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('regulations.table.lawName'),
    key: 'law_name',
    minWidth: 200,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('regulations.table.category'),
    key: 'category',
    width: 120,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('common.fields.status'),
    key: 'status',
    width: 100,
    align: 'center',
    render: (row) => {
      const status = statusMap[row.status] || {
        label: row.status,
        type: 'info' as const,
      }
      return h(
        NTag,
        {
          size: 'small',
          type: status.type,
        },
        { default: () => status.label },
      )
    },
  },
  {
    title: t('regulations.table.chapterCount'),
    key: 'total_chapters',
    width: 90,
    align: 'center',
  },
  {
    title: t('regulations.table.articleCount'),
    key: 'total_articles',
    width: 90,
    align: 'center',
  },
  {
    title: t('regulations.table.scenarioCount'),
    key: 'total_scenarios',
    width: 90,
    align: 'center',
  },
  {
    title: t('regulations.table.lastUpdated'),
    key: 'last_updated',
    width: 120,
    render: (row) => {
      return row.last_updated || '-'
    },
  },
  {
    title: t('common.fields.createdAt'),
    key: 'created_at',
    width: 180,
    render: (row) => {
      return formatDateTime(row.created_at)
    },
  },
  {
    title: t('common.fields.actions'),
    key: 'actions',
    width: 280,
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
              { default: () => t('common.actions.view') },
            ),
            h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                quaternary: true,
                onClick: () => handleExport(row),
              },
              { default: () => t('common.actions.export') },
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
                    { default: () => t('common.actions.delete') },
                  ),
                default: () => t('regulations.table.deleteConfirm'),
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
      :scroll-x="1400"
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
          {{ $t('regulations.table.totalItems', { count: itemCount }) }}
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
