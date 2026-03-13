import type { PaginationMeta } from '@/types/api'
import type { UserListParams, UserResponse } from '@/types/user'
import { ref } from 'vue'
import { getUserList } from '@/api/users'
import { message } from '@/utils/message'
import i18n from '@/i18n'

const { t } = i18n.global

export function useUserManagement() {
  const loading = ref(false)
  const users = ref<UserResponse[]>([])
  const pagination = ref<PaginationMeta>({
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 0,
  })

  const loadUsers = async (params: UserListParams = {}) => {
    loading.value = true
    try {
      const mergedParams = {
        page: pagination.value.page,
        page_size: pagination.value.page_size,
        ...params,
      }

      const response = await getUserList(mergedParams)
      users.value = response.items
      pagination.value = response.pagination
    }
    catch (error: any) {
      message.error(error.message || t('users.loadFailed'))
      throw error
    }
    finally {
      loading.value = false
    }
  }

  const handlePageChange = async (page: number) => {
    pagination.value.page = page
    await loadUsers()
  }

  const handlePageSizeChange = async (pageSize: number) => {
    pagination.value.page_size = pageSize
    pagination.value.page = 1
    await loadUsers()
  }

  return {
    loading,
    users,
    pagination,
    loadUsers,
    handlePageChange,
    handlePageSizeChange,
  }
}
