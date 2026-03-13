<script setup lang="ts">
import type { ProcessingStatus } from '@/types/dataEngineering'
import { NAlert, NSpin } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()

// 狀態標題
const statusTitle = computed(() => {
  switch (props.status) {
    case 'idle':
      return t('dataEngineering.status.idle')
    case 'processing':
      return t('dataEngineering.status.processing')
    case 'success':
      return t('dataEngineering.status.success')
    case 'error':
      return t('dataEngineering.status.error')
    default:
      return t('dataEngineering.status.unknown')
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
    return t('dataEngineering.status.processingMessage')
  }
  if (props.status === 'success') {
    const cacheInfo = props.fromCache ? t('dataEngineering.status.fromCache') : ''
    const timeInfo = props.processingTime
      ? t('dataEngineering.status.timeTaken', { time: props.processingTime.toFixed(2) })
      : ''
    return t('dataEngineering.status.successMessage', { cacheInfo, timeInfo })
  }
  if (props.status === 'error') {
    return props.error || t('dataEngineering.status.errorMessage')
  }
  return t('dataEngineering.status.idleMessage')
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
