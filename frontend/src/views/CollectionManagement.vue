<script setup lang="ts">
import type { PaginationMeta } from '@/types/api'
import type {
  Collection,
  CollectionCreateRequest,
  CollectionListParams,
  CollectionUpdateRequest,
} from '@/types/collection'
import { FolderOpenOutline as CollectionIcon } from '@vicons/ionicons5'
import { NButton, NIcon } from 'naive-ui'
import { onMounted, ref } from 'vue'
import {
  createCollection,
  deleteCollection,
  getCollectionList,
  updateCollection,
} from '@/api/collections'
import CollectionFilters from '@/components/collections/CollectionFilters.vue'
import CollectionForm from '@/components/collections/CollectionForm.vue'
import CollectionTable from '@/components/collections/CollectionTable.vue'
import { message } from '@/utils/message'

// 狀態
const loading = ref(false)
const collections = ref<Collection[]>([])
const pagination = ref<PaginationMeta>({
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 0,
})

// 篩選條件
const currentFilters = ref<CollectionListParams>({})

// 彈窗狀態
const showFormModal = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const currentCollection = ref<Collection | null>(null)

// 載入 Collection 列表
async function loadCollections() {
  loading.value = true
  try {
    const params: CollectionListParams = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ...currentFilters.value,
    }

    const response = await getCollectionList(params)

    collections.value = response.items
    pagination.value = response.pagination
  }
  catch (error: any) {
    console.error('載入 Collection 列表失敗:', error)
    message.error(error.message || '載入 Collection 列表失敗')
  }
  finally {
    loading.value = false
  }
}

// 處理搜尋
function handleSearch(filters: CollectionListParams) {
  currentFilters.value = filters
  pagination.value.page = 1 // 重置頁碼
  loadCollections()
}

// 處理重置
function handleReset() {
  currentFilters.value = {}
  pagination.value.page = 1 // 重置頁碼
  loadCollections()
}

// 處理頁碼變更
function handlePageChange(page: number) {
  pagination.value.page = page
  loadCollections()
}

// 處理每頁數量變更
function handlePageSizeChange(pageSize: number) {
  pagination.value.page_size = pageSize
  pagination.value.page = 1 // 重置頁碼
  loadCollections()
}

// 開啟新增 Collection 彈窗
function handleAddCollection() {
  formMode.value = 'create'
  currentCollection.value = null
  showFormModal.value = true
}

// 開啟編輯 Collection 彈窗
function handleEditCollection(collection: Collection) {
  formMode.value = 'edit'
  currentCollection.value = collection
  showFormModal.value = true
}

// 處理表單提交
async function handleFormSubmit(data: CollectionCreateRequest | CollectionUpdateRequest) {
  try {
    if (formMode.value === 'create') {
      // 建立 Collection
      await createCollection(data as CollectionCreateRequest)
      message.success('Collection 建立成功')
    }
    else {
      // 更新 Collection
      if (!currentCollection.value)
        return
      await updateCollection(currentCollection.value.id, data as CollectionUpdateRequest)
      message.success('Collection 更新成功')
    }

    showFormModal.value = false
    loadCollections()
  }
  catch (error: any) {
    console.error('操作失敗:', error)
    message.error(error.message || '操作失敗')
  }
}

// 處理刪除 Collection
async function handleDeleteCollection(collectionId: number) {
  try {
    await deleteCollection(collectionId)
    message.success('Collection 刪除成功')
    loadCollections()
  }
  catch (error: any) {
    console.error('刪除 Collection 失敗:', error)
    message.error(error.message || '刪除 Collection 失敗')
  }
}

// 頁面載入時獲取 Collection 列表
onMounted(() => {
  loadCollections()
})
</script>

<template>
  <div class="collection-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          Collection 管理
        </h1>
        <p class="page-description">
          管理文件集合、分塊策略與資料集
        </p>
      </div>
      <div class="header-actions">
        <NButton type="primary" size="large" @click="handleAddCollection">
          <template #icon>
            <NIcon>
              <CollectionIcon />
            </NIcon>
          </template>
          新增 Collection
        </NButton>
      </div>
    </div>

    <!-- 篩選區域 -->
    <div class="filters-section">
      <CollectionFilters
        @search="handleSearch"
        @reset="handleReset"
      />
    </div>

    <!-- 表格區域 -->
    <div class="table-section">
      <CollectionTable
        :data="collections"
        :pagination="pagination"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        @edit="handleEditCollection"
        @delete="handleDeleteCollection"
      />
    </div>

    <!-- 新增/編輯 Collection 彈窗 -->
    <CollectionForm
      v-model:show="showFormModal"
      :mode="formMode"
      :collection="currentCollection"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<style scoped>
.collection-management {
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
  .collection-management {
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
