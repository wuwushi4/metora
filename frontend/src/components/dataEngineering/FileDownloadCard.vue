<script setup lang="ts">
import type { LawProcessResponse } from '@/types/dataEngineering'
import { DownloadOutline } from '@vicons/ionicons5'
import { NButton, NCard, NDescriptions, NDescriptionsItem, NSpace, NTag } from 'naive-ui'
import { useFileDownload } from '@/composables/useFileDownload'
import { message } from '@/utils/message'

interface Props {
  result: LawProcessResponse
}

const props = defineProps<Props>()

const { downloadMarkdownAsFile, downloadJsonAsFile } = useFileDownload()

// 下載 Markdown 檔案
function handleDownloadMarkdown() {
  try {
    downloadMarkdownAsFile(props.result.md_content, props.result.md_filename)
    message.success(`已下載 ${props.result.md_filename}`)
  }
  catch (error) {
    message.error('下載 Markdown 檔案失敗')
    console.error('下載失敗:', error)
  }
}

// 下載 JSON 檔案
function handleDownloadJson() {
  try {
    downloadJsonAsFile(props.result.json_content, props.result.json_filename)
    message.success(`已下載 ${props.result.json_filename}`)
  }
  catch (error) {
    message.error('下載 JSON 檔案失敗')
    console.error('下載失敗:', error)
  }
}
</script>

<template>
  <NCard title="處理結果" class="result-card">
    <template #header-extra>
      <NTag v-if="result.from_cache" type="info" size="small">
        來自快取
      </NTag>
    </template>

    <!-- 法規資訊 -->
    <NDescriptions label-placement="left" :column="1" bordered class="mb-4">
      <NDescriptionsItem label="法規編號">
        {{ result.pcode }}
      </NDescriptionsItem>
      <NDescriptionsItem label="法規名稱">
        {{ result.law_name }}
      </NDescriptionsItem>
      <NDescriptionsItem label="章數">
        {{ result.statistics.chapters }}
      </NDescriptionsItem>
      <NDescriptionsItem label="條數">
        {{ result.statistics.articles }}
      </NDescriptionsItem>
      <NDescriptionsItem label="項數">
        {{ result.statistics.items }}
      </NDescriptionsItem>
      <NDescriptionsItem label="款數">
        {{ result.statistics.subitems }}
      </NDescriptionsItem>
      <NDescriptionsItem v-if="result.processing_time" label="處理時間">
        {{ result.processing_time.toFixed(2) }} 秒
      </NDescriptionsItem>
    </NDescriptions>

    <!-- 下載按鈕 -->
    <NSpace>
      <NButton type="primary" @click="handleDownloadMarkdown">
        <template #icon>
          <DownloadOutline />
        </template>
        下載 Markdown 檔案
      </NButton>
      <NButton type="info" @click="handleDownloadJson">
        <template #icon>
          <DownloadOutline />
        </template>
        下載 JSON 檔案
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.result-card {
  margin-top: 1.5rem;
}
</style>
