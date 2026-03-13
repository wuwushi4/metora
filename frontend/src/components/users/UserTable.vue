<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import type { PaginationMeta } from '@/types/api'
import type { UserResponse } from '@/types/user'
import {
  NBadge,
  NButton,
  NDataTable,
  NPagination,
  NPopconfirm,
  NSpace,
  NTag,
} from 'naive-ui'
import { h } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/date'
import { message } from '@/utils/message'

interface Props {
  data: UserResponse[]
  pagination: PaginationMeta
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [pageSize: number]
  'edit': [user: UserResponse]
  'delete': [userId: number]
  'assignRoles': [user: UserResponse]
}>()

const { t } = useI18n()
const authStore = useAuthStore()

// 檢查是否為當前使用者
function isCurrentUser(userId: number): boolean {
  return authStore.user?.id === userId
}

// 檢查是否可以刪除使用者
function canDeleteUser(user: UserResponse): boolean {
  // 不能刪除自己
  if (isCurrentUser(user.id))
    return false
  // 不能刪除超級管理員
  if (user.is_superuser)
    return false
  return true
}

// 處理編輯
function handleEdit(user: UserResponse) {
  emit('edit', user)
}

// 處理刪除
function handleDelete(user: UserResponse) {
  if (!canDeleteUser(user)) {
    if (isCurrentUser(user.id)) {
      message.warning(t('users.table.cannotDeleteSelf'))
    }
    else if (user.is_superuser) {
      message.warning(t('users.table.cannotDeleteSuperAdmin'))
    }
    return
  }
  emit('delete', user.id)
}

// 處理角色分配
function handleAssignRoles(user: UserResponse) {
  emit('assignRoles', user)
}

// 表格欄位定義
const columns: DataTableColumns<UserResponse> = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: t('users.table.username'),
    key: 'username',
    minWidth: 120,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('users.table.email'),
    key: 'email',
    minWidth: 200,
    ellipsis: {
      tooltip: true,
    },
  },
  {
    title: t('users.table.fullName'),
    key: 'full_name',
    minWidth: 120,
    ellipsis: {
      tooltip: true,
    },
    render: (row) => {
      return row.full_name || '-'
    },
  },
  {
    title: t('common.fields.role'),
    key: 'roles',
    minWidth: 150,
    render: (row) => {
      if (!row.roles || row.roles.length === 0) {
        return h(NTag, { size: 'small', type: 'default' }, { default: () => t('common.fields.none') })
      }
      return h(
        NSpace,
        { size: 4 },
        {
          default: () =>
            row.roles.map(role =>
              h(
                NTag,
                {
                  size: 'small',
                  type: role === 'admin' ? 'error' : 'info',
                },
                { default: () => role },
              ),
            ),
        },
      )
    },
  },
  {
    title: t('common.fields.status'),
    key: 'is_active',
    width: 100,
    align: 'center',
    render: (row) => {
      return h(
        NBadge,
        {
          dot: true,
          type: row.is_active ? 'success' : 'default',
        },
        {
          default: () => (row.is_active ? t('common.status.enabled') : t('common.status.disabled')),
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
    width: 220,
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
                type: 'primary',
                quaternary: true,
                onClick: () => handleEdit(row),
              },
              { default: () => t('common.actions.edit') },
            ),
            h(
              NButton,
              {
                size: 'small',
                type: 'info',
                quaternary: true,
                onClick: () => handleAssignRoles(row),
              },
              { default: () => t('users.table.assignRoles') },
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
                      disabled: !canDeleteUser(row),
                    },
                    { default: () => t('common.actions.delete') },
                  ),
                default: () => t('users.table.deleteConfirm'),
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
          {{ $t('users.table.totalItems', { count: itemCount }) }}
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
