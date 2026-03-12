<script setup lang="ts">
import type { PaginationMeta } from '@/types/api'
import type { Collection } from '@/types/collection'
import type { Dataset, DatasetListParams } from '@/types/dataset'
import { ArrowBackOutline as BackIcon, RefreshOutline as RefreshIcon, CloudUploadOutline as UploadIcon } from '@vicons/ionicons5'
import { NButton, NCard, NDescriptions, NDescriptionsItem, NIcon, NSpin, NTag } from 'naive-ui'
import { useBreakpoints } from '@vueuse/core'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCollectionById } from '@/api/collections'
import { deleteDataset, getDatasetList, uploadDataset } from '@/api/datasets'
import DatasetTable from '@/components/collections/DatasetTable.vue'
import DatasetUploadModal from '@/components/collections/DatasetUploadModal.vue'
import { message } from '@/utils/message'

const route = useRoute()
const router = useRouter()

// 狀態
const loading = ref(false)
const datasetsLoading = ref(false)
const uploadModalVisible = ref(false)
const collection = ref<Collection | null>(null)
const datasets = ref<Dataset[]>([])
const pagination = ref<PaginationMeta>({
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 0,
})

const breakpoints = useBreakpoints({ mobile: 768 })
const descriptionColumn = computed(() => breakpoints.smaller('mobile').value ? 1 : 2)

// Collection ID
const collectionId = computed(() => {
  return Number(route.params.id)
})

// 分塊策略顯示名稱映射
const chunkingStrategyMap: Record<string, { label: string, type: 'info' | 'success' | 'warning' }> = {
  qa_multi_representation: { label: 'QA 多重表徵', type: 'info' },
  regulation_hierarchical: { label: '法規-階層式', type: 'success' },
  regulation_context_enriched: { label: '法規-情境增強', type: 'success' },
  regulation_manual_scenario: { label: '法規-情境描述', type: 'success' },
  recursive_text: { label: '遞迴文字分塊', type: 'warning' },
}

// 載入 Collection 資訊
async function loadCollection() {
  loading.value = true
  try {
    collection.value = await getCollectionById(collectionId.value)
  }
  catch (error: any) {
    console.error('載入 Collection 失敗:', error)
    message.error(error.message || '載入 Collection 失敗')
    // 載入失敗返回列表頁
    router.push('/collections')
  }
  finally {
    loading.value = false
  }
}

// 載入 Dataset 列表
async function loadDatasets() {
  datasetsLoading.value = true
  try {
    const params: DatasetListParams = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      collection_id: collectionId.value,
    }

    const response = await getDatasetList(params)

    datasets.value = response.items
    pagination.value = response.pagination
  }
  catch (error: any) {
    console.error('載入 Dataset 列表失敗:', error)
    message.error(error.message || '載入 Dataset 列表失敗')
  }
  finally {
    datasetsLoading.value = false
  }
}

// 處理頁碼變更
function handlePageChange(page: number) {
  pagination.value.page = page
  loadDatasets()
}

// 處理每頁數量變更
function handlePageSizeChange(pageSize: number) {
  pagination.value.page_size = pageSize
  pagination.value.page = 1
  loadDatasets()
}

// 返回列表頁
function handleBack() {
  router.push('/collections')
}

// 開啟上傳彈窗
function handleOpenUpload() {
  uploadModalVisible.value = true
}

// 處理檔案上傳
async function handleUpload(files: File[], chunkingOptions?: { chunkSize: number, chunkOverlap: number }) {
  try {
    // 逐個上傳檔案
    for (const file of files) {
      await uploadDataset(collectionId.value, file, chunkingOptions
        ? { chunkSize: chunkingOptions.chunkSize, chunkOverlap: chunkingOptions.chunkOverlap }
        : undefined)
    }

    message.success(`成功上傳 ${files.length} 個檔案，正在處理向量化...`)
    uploadModalVisible.value = false

    // 重新載入列表
    await loadCollection()
    await loadDatasets()
  }
  catch (error: any) {
    console.error('上傳檔案失敗:', error)
    message.error(error.message || '上傳檔案失敗')
  }
}

// 處理刪除 Dataset
async function handleDeleteDataset(datasetId: number) {
  try {
    await deleteDataset(datasetId)
    message.success('Dataset 刪除成功')

    // 重新載入
    await loadCollection()
    await loadDatasets()
  }
  catch (error: any) {
    console.error('刪除 Dataset 失敗:', error)
    message.error(error.message || '刪除 Dataset 失敗')
  }
}

// 手動重新整理
async function handleRefresh() {
  await Promise.all([loadCollection(), loadDatasets()])
  message.success('重新整理成功')
}

// 頁面載入時獲取資料
onMounted(async () => {
  await loadCollection()
  await loadDatasets()
})
</script>

<template>
  <div class="collection-detail">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-left">
        <NButton @click="handleBack">
          <template #icon>
            <NIcon :component="BackIcon" />
          </template>
          返回列表
        </NButton>
        <div class="header-content">
          <h1 class="page-title">
            {{ collection?.name || 'Loading...' }}
          </h1>
          <p class="page-description">
            Collection 詳細資訊與 Dataset 管理
          </p>
        </div>
      </div>
      <div class="header-actions">
        <NButton @click="handleRefresh">
          <template #icon>
            <NIcon>
              <RefreshIcon />
            </NIcon>
          </template>
          重新整理
        </NButton>
        <NButton type="primary" @click="handleOpenUpload">
          <template #icon>
            <NIcon>
              <UploadIcon />
            </NIcon>
          </template>
          上傳檔案
        </NButton>
      </div>
    </div>

    <!-- Collection 資訊卡片 -->
    <NSpin :show="loading">
      <NCard v-if="collection" title="Collection 資訊" class="info-card">
        <NDescriptions :column="descriptionColumn" label-placement="left">
          <NDescriptionsItem label="ID">
            {{ collection.id }}
          </NDescriptionsItem>
          <NDescriptionsItem label="名稱">
            {{ collection.name }}
          </NDescriptionsItem>
          <NDescriptionsItem label="描述">
            {{ collection.description || '-' }}
          </NDescriptionsItem>
          <NDescriptionsItem label="分塊策略">
            <NTag
              :type="chunkingStrategyMap[collection.chunking_strategy]?.type || 'info'"
              size="small"
            >
              {{ chunkingStrategyMap[collection.chunking_strategy]?.label || collection.chunking_strategy }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem label="Dataset 數量">
            {{ collection.dataset_count }}
          </NDescriptionsItem>
          <NDescriptionsItem label="所有者">
            {{ collection.owner?.full_name || collection.owner?.username || `使用者 #${collection.user_id}` }}
          </NDescriptionsItem>
          <NDescriptionsItem label="建立時間">
            {{ new Date(collection.created_at).toLocaleString('zh-TW') }}
          </NDescriptionsItem>
          <NDescriptionsItem label="更新時間">
            {{ new Date(collection.updated_at).toLocaleString('zh-TW') }}
          </NDescriptionsItem>
        </NDescriptions>
      </NCard>
    </NSpin>

    <!-- Dataset 列表 -->
    <div class="datasets-section">
      <div class="section-header">
        <h2 class="section-title">
          Dataset 列表
        </h2>
      </div>
      <DatasetTable
        :data="datasets"
        :pagination="pagination"
        :loading="datasetsLoading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        @delete="handleDeleteDataset"
      />
    </div>

    <!-- 上傳檔案彈窗 -->
    <DatasetUploadModal
      v-model:show="uploadModalVisible"
      :collection-id="collectionId"
      :chunking-strategy="collection?.chunking_strategy ?? ''"
      @upload="handleUpload"
    />
  </div>
</template>

<style scoped>
.collection-detail {
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

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
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

.info-card {
  margin-bottom: 24px;
}

.datasets-section {
  margin-bottom: 24px;
}

.section-header {
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

@media (max-width: 768px) {
  .collection-detail {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-left {
    width: 100%;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .header-actions button {
    flex: 1;
  }
}
</style>
