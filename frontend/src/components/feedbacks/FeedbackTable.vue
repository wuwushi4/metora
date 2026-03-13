<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import type { PaginationMeta } from '@/types/api'
import type { FeedbackListItem } from '@/types/feedback'
import { NButton, NDataTable, NPagination, NSpace, NTag } from 'naive-ui'
import { h } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@/utils/date'

interface Props {
  data: FeedbackListItem[]
  pagination: PaginationMeta
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
}>()

const { t } = useI18n()
const router = useRouter()

// 處理查看詳情
function handleView(feedback: FeedbackListItem) {
  router.push(`/feedbacks/${feedback.id}`)
}

// 表格欄位定義
const columns: DataTableColumns<FeedbackListItem> = [
  {
    title: t('feedbacks.table.user'),
    key: 'user',
    width: 150,
    render: (row) => {
      return row.user.full_name || row.user.username
    },
  },
  {
    title: t('feedbacks.table.messagePreview'),
    key: 'message_preview',
    minWidth: 250,
    ellipsis: {
      tooltip: true,
    },
    render: (row) => {
      return h(
        NSpace,
        { align: 'center', size: 8 },
        {
          default: () => [
            row.message_preview,
            row.is_interrupted
              ? h(
                  NTag,
                  {
                    size: 'small',
                    type: 'warning',
                    bordered: false,
                  },
                  { default: () => t('feedbacks.table.interrupted') },
                )
              : null,
          ].filter(Boolean),
        },
      )
    },
  },
  {
    title: t('feedbacks.table.agentType'),
    key: 'graph_type',
    width: 120,
    align: 'center',
    render: (row) => {
      const graphTypeLabels: Record<string, string> = {
        base_graph: t('feedbacks.filters.graphTypes.base_graph'),
        rag_graph: t('feedbacks.filters.graphTypes.rag_graph'),
        regulation_graph: t('feedbacks.filters.graphTypes.regulation_graph'),
      }
      const label = graphTypeLabels[row.graph_type] || row.graph_type
      return h(
        NTag,
        {
          size: 'small',
          type: 'info',
        },
        {
          default: () => label,
        },
      )
    },
  },
  {
    title: t('feedbacks.table.collection'),
    key: 'collection_names',
    width: 200,
    render: (row) => {
      if (!row.collection_names || row.collection_names.length === 0) {
        return '-'
      }
      return h(
        NSpace,
        { size: 4 },
        {
          default: () =>
            row.collection_names.map(name =>
              h(NTag, { size: 'small', type: 'success' }, { default: () => name }),
            ),
        },
      )
    },
  },
  {
    title: t('feedbacks.table.feedbackType'),
    key: 'feedback_type',
    width: 120,
    align: 'center',
    render: (row) => {
      return h(
        NTag,
        {
          size: 'small',
          type: row.feedback_type === 'thumbs_up' ? 'success' : 'error',
        },
        {
          default: () => (row.feedback_type === 'thumbs_up' ? t('feedbacks.filters.like') : t('feedbacks.filters.dislike')),
        },
      )
    },
  },
  {
    title: t('feedbacks.table.issueLabels'),
    key: 'issue_tags',
    width: 200,
    render: (row) => {
      if (!row.issue_tags || row.issue_tags.length === 0) {
        return '-'
      }
      return h(
        NSpace,
        { size: 4 },
        {
          default: () =>
            row.issue_tags!.map(tag =>
              h(NTag, { size: 'small', type: 'warning' }, { default: () => tag }),
            ),
        },
      )
    },
  },
  {
    title: t('feedbacks.table.reviewStatus'),
    key: 'is_reviewed',
    width: 120,
    align: 'center',
    render: (row) => {
      return h(
        NTag,
        {
          size: 'small',
          type: row.is_reviewed ? 'info' : 'default',
        },
        {
          default: () => (row.is_reviewed ? t('feedbacks.filters.reviewed') : t('feedbacks.filters.notReviewed')),
        },
      )
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
    width: 100,
    fixed: 'right',
    align: 'center',
    render: (row) => {
      return h(
        NButton,
        {
          size: 'small',
          type: 'primary',
          text: true,
          onClick: () => handleView(row),
        },
        { default: () => t('common.actions.viewDetail') },
      )
    },
  },
]
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
        @update:page="emit('update:page', $event)"
        @update:page-size="emit('update:pageSize', $event)"
      >
        <template #prefix="{ itemCount }">
          {{ $t('feedbacks.table.totalItems', { count: itemCount }) }}
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
