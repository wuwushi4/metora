<script setup lang="ts">
import type { ProcessingStatus } from '@/types/dataEngineering'
import { NAlert, NSpin } from 'naive-ui'
import { computed } from 'vue'

interface Props {
  status: ProcessingStatus
  error?: string
  processingTime?: number
  fromCache?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  status: 'idle',
  error: undefined,
  processingTime: undefined,
  fromCache: false,
})

// 狀態標題
const statusTitle = computed(() => {
  switch (props.status) {
    case 'idle':
      return '等待處理'
    case 'processing':
      return '處理中...'
    case 'success':
      return '處理成功'
    case 'error':
      return '處理失敗'
    default:
      return '未知狀態'
  }
})

// 狀態類型（用於 Alert 組件）
const statusType = computed(() => {
  switch (props.status) {
    case 'processing':
      return 'info'
    case 'success':
      return 'success'
    case 'error':
      return 'error'
    default:
      return 'default'
  }
})

// 狀態訊息
const statusMessage = computed(() => {
  if (props.status === 'processing') {
    return '正在爬取法規資料並轉換為 Markdown 和 JSON 格式...'
  }
  if (props.status === 'success') {
    const cacheInfo = props.fromCache ? '（來自快取）' : ''
    const timeInfo = props.processingTime
      ? `，耗時 ${props.processingTime.toFixed(2)} 秒`
      : ''
    return `法規資料處理完成${cacheInfo}${timeInfo}，請在下方下載檔案。`
  }
  if (props.status === 'error') {
    return props.error || '發生未知錯誤，請稍後再試。'
  }
  return '請在上方輸入法規編號開始處理。'
})
</script>

<template>
  <div v-if="status !== 'idle'" class="process-status">
    <NSpin v-if="status === 'processing'" size="small" class="mb-4">
      <template #description>
        {{ statusMessage }}
      </template>
    </NSpin>

    <NAlert
      v-else
      :title="statusTitle"
      :type="statusType"
      class="mb-4"
    >
      {{ statusMessage }}
    </NAlert>
  </div>
</template>

<style scoped>
.process-status {
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
}
</style>
