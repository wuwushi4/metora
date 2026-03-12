<script setup lang="ts">
import type { PaginationMeta } from '@/types/api'
import type {
  AssignRolesRequest,
  UserCreateRequest,
  UserListParams,
  UserResponse,
  UserUpdateRequest,
} from '@/types/user'
import { PersonAddOutline as AddUserIcon } from '@vicons/ionicons5'
import { NButton, NIcon } from 'naive-ui'
import { onMounted, ref } from 'vue'
import {
  assignRoles,
  createUser,
  deleteUser,
  getUserList,
  updateUser,
} from '@/api/users'
import RoleAssignModal from '@/components/users/RoleAssignModal.vue'
import UserFilters from '@/components/users/UserFilters.vue'
import UserForm from '@/components/users/UserForm.vue'
import UserTable from '@/components/users/UserTable.vue'
import { message } from '@/utils/message'

// 狀態
const loading = ref(false)
const users = ref<UserResponse[]>([])
const pagination = ref<PaginationMeta>({
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 0,
})

// 篩選條件
const currentFilters = ref<UserListParams>({})

// 彈窗狀態
const showFormModal = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const currentUser = ref<UserResponse | null>(null)

const showRoleModal = ref(false)
const roleUser = ref<UserResponse | null>(null)

// 載入使用者列表
async function loadUsers() {
  loading.value = true
  try {
    const params: UserListParams = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ...currentFilters.value,
    }

    const response = await getUserList(params)

    users.value = response.items
    pagination.value = response.pagination
  }
  catch (error: any) {
    console.error('載入使用者列表失敗:', error)
    message.error(error.message || '載入使用者列表失敗')
  }
  finally {
    loading.value = false
  }
}

// 處理搜尋
function handleSearch(filters: UserListParams) {
  currentFilters.value = filters
  pagination.value.page = 1 // 重置頁碼
  loadUsers()
}

// 處理重置
function handleReset() {
  currentFilters.value = {}
  pagination.value.page = 1 // 重置頁碼
  loadUsers()
}

// 處理頁碼變更
function handlePageChange(page: number) {
  pagination.value.page = page
  loadUsers()
}

// 處理每頁數量變更
function handlePageSizeChange(pageSize: number) {
  pagination.value.page_size = pageSize
  pagination.value.page = 1 // 重置頁碼
  loadUsers()
}

// 開啟新增使用者彈窗
function handleAddUser() {
  formMode.value = 'create'
  currentUser.value = null
  showFormModal.value = true
}

// 開啟編輯使用者彈窗
function handleEditUser(user: UserResponse) {
  formMode.value = 'edit'
  currentUser.value = user
  showFormModal.value = true
}

// 處理表單提交
async function handleFormSubmit(data: UserCreateRequest | UserUpdateRequest) {
  try {
    if (formMode.value === 'create') {
      // 建立使用者
      await createUser(data as UserCreateRequest)
      message.success('使用者建立成功')
    }
    else {
      // 更新使用者
      if (!currentUser.value)
        return
      await updateUser(currentUser.value.id, data as UserUpdateRequest)
      message.success('使用者更新成功')
    }

    showFormModal.value = false
    loadUsers()
  }
  catch (error: any) {
    console.error('操作失敗:', error)
    message.error(error.message || '操作失敗')
  }
}

// 處理刪除使用者
async function handleDeleteUser(userId: number) {
  try {
    await deleteUser(userId)
    message.success('使用者刪除成功')
    loadUsers()
  }
  catch (error: any) {
    console.error('刪除使用者失敗:', error)
    message.error(error.message || '刪除使用者失敗')
  }
}

// 開啟角色分配彈窗
function handleAssignRoles(user: UserResponse) {
  roleUser.value = user
  showRoleModal.value = true
}

// 處理角色分配提交
async function handleRoleSubmit(data: AssignRolesRequest) {
  try {
    if (!roleUser.value)
      return

    await assignRoles(roleUser.value.id, data)
    message.success('角色分配成功')
    showRoleModal.value = false
    loadUsers()
  }
  catch (error: any) {
    console.error('角色分配失敗:', error)
    message.error(error.message || '角色分配失敗')
  }
}

// 頁面載入時獲取使用者列表
onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="user-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          使用者管理
        </h1>
        <p class="page-description">
          管理系統使用者帳號、角色與權限
        </p>
      </div>
      <div class="header-actions">
        <NButton type="primary" size="large" @click="handleAddUser">
          <template #icon>
            <NIcon>
              <AddUserIcon />
            </NIcon>
          </template>
          新增使用者
        </NButton>
      </div>
    </div>

    <!-- 篩選區域 -->
    <div class="filters-section">
      <UserFilters
        @search="handleSearch"
        @reset="handleReset"
      />
    </div>

    <!-- 表格區域 -->
    <div class="table-section">
      <UserTable
        :data="users"
        :pagination="pagination"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        @edit="handleEditUser"
        @delete="handleDeleteUser"
        @assign-roles="handleAssignRoles"
      />
    </div>

    <!-- 新增/編輯使用者彈窗 -->
    <UserForm
      v-model:show="showFormModal"
      :mode="formMode"
      :user="currentUser"
      @submit="handleFormSubmit"
    />

    <!-- 角色分配彈窗 -->
    <RoleAssignModal
      v-model:show="showRoleModal"
      :user="roleUser"
      @submit="handleRoleSubmit"
    />
  </div>
</template>

<style scoped>
.user-management {
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e5e7eb;
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.page-description {
  margin: 8px 0 0;
  font-size: 0.9375rem;
  color: #6b7280;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filters-section {
  margin-bottom: 24px;
}

.table-section {
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .user-management {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions button {
    flex: 1;
  }
}
</style>
