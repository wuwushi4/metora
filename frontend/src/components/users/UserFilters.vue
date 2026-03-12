<script setup lang="ts">
import type { UserListParams } from '@/types/user'
import { NButton, NInput, NSelect, NSpace } from 'naive-ui'
import { ref } from 'vue'

const emit = defineEmits<{
  search: [params: UserListParams]
  reset: []
}>()

// 篩選條件
const filters = ref({
  username: '' as string,
  email: '' as string,
  is_active: '' as string,
  role: '' as string,
})

// 狀態選項
const statusOptions = [
  { label: '全部', value: '' },
  { label: '啟用', value: 'true' },
  { label: '停用', value: 'false' },
]

// 角色選項
const roleOptions = [
  { label: '全部', value: '' },
  { label: '管理員', value: 'admin' },
  { label: '一般使用者', value: 'user' },
  { label: '編輯者', value: 'editor' },
  { label: '檢視者', value: 'viewer' },
]

// 處理搜尋
function handleSearch() {
  // 移除空值
  const params: UserListParams = {}
  if (filters.value.username && filters.value.username !== '')
    params.username = filters.value.username
  if (filters.value.email && filters.value.email !== '')
    params.email = filters.value.email
  if (filters.value.is_active && filters.value.is_active !== '') {
    // 將字串轉換為 boolean
    params.is_active = filters.value.is_active === 'true'
  }
  if (filters.value.role && filters.value.role !== '')
    params.role = filters.value.role

  emit('search', params)
}

// 處理重置
function handleReset() {
  filters.value = {
    username: '',
    email: '',
    is_active: '',
    role: '',
  }
  emit('reset')
}
</script>

<template>
  <div class="filters-container">
    <NSpace vertical :size="16">
      <!-- 第一行：使用者名稱和電子郵件 -->
      <NSpace :size="16">
        <div class="filter-item">
          <label class="filter-label">使用者名稱</label>
          <NInput
            v-model:value="filters.username"
            placeholder="搜尋使用者名稱"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">電子郵件</label>
          <NInput
            v-model:value="filters.email"
            placeholder="搜尋電子郵件"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>
      </NSpace>

      <!-- 第二行：狀態、角色和操作按鈕 -->
      <NSpace :size="16" align="center">
        <div class="filter-item">
          <label class="filter-label">狀態</label>
          <NSelect
            v-model:value="filters.is_active"
            :options="statusOptions"
            placeholder="選擇狀態"
            clearable
            style="width: 160px"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">角色</label>
          <NSelect
            v-model:value="filters.role"
            :options="roleOptions"
            placeholder="選擇角色"
            clearable
            style="width: 160px"
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
