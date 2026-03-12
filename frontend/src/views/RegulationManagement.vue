<script setup lang="ts">
import type { PaginationMeta } from '@/types/api'
import type {
  Regulation,
  RegulationContent,
  RegulationListParams,
} from '@/types/regulation'
import { CloudUploadOutline as UploadIcon } from '@vicons/ionicons5'
import { NButton, NIcon } from 'naive-ui'
import { onMounted, ref } from 'vue'
import {
  deleteRegulation,
  exportRegulation,
  getRegulationList,
  uploadRegulation,
} from '@/api/regulations'
import RegulationFilters from '@/components/regulations/RegulationFilters.vue'
import RegulationTable from '@/components/regulations/RegulationTable.vue'
import RegulationUploadModal from '@/components/regulations/RegulationUploadModal.vue'
import { message } from '@/utils/message'

// 狀態
const loading = ref(false)
const regulations = ref<Regulation[]>([])
const pagination = ref<PaginationMeta>({
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 0,
})

// 篩選條件
const currentFilters = ref<RegulationListParams>({})

// 上傳彈窗狀態
const showUploadModal = ref(false)

// 載入法規列表
async function loadRegulations() {
  loading.value = true
  try {
    const params: RegulationListParams = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ...currentFilters.value,
    }

    const response = await getRegulationList(params)

    regulations.value = response.items
    pagination.value = response.pagination
  }
  catch (error: any) {
    console.error('載入法規列表失敗:', error)
    message.error(error.message || '載入法規列表失敗')
  }
  finally {
    loading.value = false
  }
}

// 處理搜尋
function handleSearch(filters: RegulationListParams) {
  currentFilters.value = filters
  pagination.value.page = 1 // 重置頁碼
  loadRegulations()
}

// 處理重置
function handleReset() {
  currentFilters.value = {}
  pagination.value.page = 1 // 重置頁碼
  loadRegulations()
}

// 處理頁碼變更
function handlePageChange(page: number) {
  pagination.value.page = page
  loadRegulations()
}

// 處理每頁數量變更
function handlePageSizeChange(pageSize: number) {
  pagination.value.page_size = pageSize
  pagination.value.page = 1 // 重置頁碼
  loadRegulations()
}

// 開啟上傳彈窗
function handleUploadRegulation() {
  showUploadModal.value = true
}

// 處理上傳提交
async function handleUploadSubmit(content: RegulationContent) {
  try {
    await uploadRegulation({ content })
    message.success('法規上傳成功')
    showUploadModal.value = false
    loadRegulations()
  }
  catch (error: any) {
    console.error('上傳法規失敗:', error)
    message.error(error.message || '上傳法規失敗')
  }
}

// 處理刪除法規
async function handleDeleteRegulation(regulationId: number) {
  try {
    await deleteRegulation(regulationId)
    message.success('法規刪除成功')
    loadRegulations()
  }
  catch (error: any) {
    console.error('刪除法規失敗:', error)
    message.error(error.message || '刪除法規失敗')
  }
}

// 處理導出法規
async function handleExportRegulation(regulation: Regulation) {
  const loadingMessage = message.loading('正在導出法規...', { duration: 0 })

  try {
    const blob = await exportRegulation(regulation.id)

    // 建立下載連結
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${regulation.law_name}_${regulation.law_code}.json`

    // 觸發下載
    document.body.appendChild(link)
    link.click()

    // 清理
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    loadingMessage.destroy()
    message.success('法規導出成功')
  }
  catch (error: any) {
    console.error('導出法規失敗:', error)
    loadingMessage.destroy()
    message.error(error.message || '導出法規失敗')
  }
}

// 頁面載入時獲取法規列表
onMounted(() => {
  loadRegulations()
})
</script>

<template>
  <div class="regulation-management">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          法規管理
        </h1>
        <p class="page-description">
          管理法規文件、章節條文與應用情境
        </p>
      </div>
      <div class="header-actions">
        <NButton type="primary" size="large" @click="handleUploadRegulation">
          <template #icon>
            <NIcon>
              <UploadIcon />
            </NIcon>
          </template>
          上傳法規
        </NButton>
      </div>
    </div>

    <!-- 篩選區域 -->
    <div class="filters-section">
      <RegulationFilters
        @search="handleSearch"
        @reset="handleReset"
      />
    </div>

    <!-- 表格區域 -->
    <div class="table-section">
      <RegulationTable
        :data="regulations"
        :pagination="pagination"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        @delete="handleDeleteRegulation"
        @export="handleExportRegulation"
      />
    </div>

    <!-- 上傳法規彈窗 -->
    <RegulationUploadModal
      v-model:show="showUploadModal"
      @upload="handleUploadSubmit"
    />
  </div>
</template>

<style scoped>
.regulation-management {
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
  .regulation-management {
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
