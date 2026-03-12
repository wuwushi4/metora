<script setup lang="ts">
import type {
  LawProcessRequest,
  LawProcessResponse,
  ProcessingStatus,
} from '@/types/dataEngineering'
import { NCard } from 'naive-ui'
import { ref } from 'vue'
import { processLaw } from '@/api/dataEngineering'
import FileDownloadCard from '@/components/dataEngineering/FileDownloadCard.vue'
import LawInputForm from '@/components/dataEngineering/LawInputForm.vue'
import ProcessStatus from '@/components/dataEngineering/ProcessStatus.vue'
import { message } from '@/utils/message'

// 處理狀態
const processingStatus = ref<ProcessingStatus>('idle')
const errorMessage = ref<string | undefined>(undefined)
const result = ref<LawProcessResponse | undefined>(undefined)

// 處理法規請求
async function handleSubmit(requestData: LawProcessRequest) {
  try {
    // 重置狀態
    processingStatus.value = 'processing'
    errorMessage.value = undefined
    result.value = undefined

    // 呼叫 API
    const response = await processLaw(requestData)

    // 更新成功狀態
    processingStatus.value = 'success'
    result.value = response

    message.success('法規處理完成')
  }
  catch (error: any) {
    // 更新錯誤狀態
    processingStatus.value = 'error'
    errorMessage.value = error.response?.data?.detail || error.message || '處理失敗，請稍後再試'

    // Naive UI 的訊息已由 error-handler 統一處理，這裡不需要再顯示
    console.error('法規處理失敗:', error)
  }
}
</script>

<template>
  <div class="law-processing-container">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1 class="page-title">
        法規爬蟲作業
      </h1>
      <p class="page-subtitle">
        輸入法規編號，自動爬取法規內容並轉換為 Markdown 和 JSON 格式 (目標網站：<a href="https://law.moj.gov.tw/Index.aspx" target="_blank">https://law.moj.gov.tw/Index.aspx</a>)。
      </p>
    </div>

    <!-- 輸入表單 -->
    <NCard title="輸入法規資訊" :bordered="false" class="form-card">
      <LawInputForm
        ref="formRef"
        :loading="processingStatus === 'processing'"
        @submit="handleSubmit"
      />
    </NCard>

    <!-- 處理狀態 -->
    <ProcessStatus
      :status="processingStatus"
      :error="errorMessage"
      :processing-time="result?.processing_time"
      :from-cache="result?.from_cache"
    />

    <!-- 處理結果 -->
    <FileDownloadCard v-if="result && processingStatus === 'success'" :result="result" />
  </div>
</template>

<style scoped>
.law-processing-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

.form-card {
  box-shadow:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);
  border-radius: 16px;
}

.form-card :deep(.n-card-header) {
  padding: 20px 24px;
  font-weight: 600;
  font-size: 1.125rem;
}

@media (max-width: 768px) {
  .law-processing-container {
    padding: 16px;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
  }

  .form-card :deep(.n-card-header) {
    padding: 16px;
    font-size: 1rem;
  }
}
</style>
