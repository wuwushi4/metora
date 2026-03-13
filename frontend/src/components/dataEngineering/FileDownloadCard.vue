<script setup lang="ts">
import type { LawProcessResponse } from '@/types/dataEngineering'
import { DownloadOutline } from '@vicons/ionicons5'
import { NButton, NCard, NDescriptions, NDescriptionsItem, NSpace, NTag } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useFileDownload } from '@/composables/useFileDownload'
import { message } from '@/utils/message'

interface Props {
  result: LawProcessResponse
}

const props = defineProps<Props>()

const { t } = useI18n()
const { downloadMarkdownAsFile, downloadJsonAsFile } = useFileDownload()

// 下載 Markdown 檔案
function handleDownloadMarkdown() {
  try {
    downloadMarkdownAsFile(props.result.md_content, props.result.md_filename)
    message.success(t('dataEngineering.result.downloaded', { filename: props.result.md_filename }))
  }
  catch (error) {
    message.error(t('dataEngineering.result.downloadMarkdownFailed'))
    console.error('下載失敗:', error)
  }
}

// 下載 JSON 檔案
function handleDownloadJson() {
  try {
    downloadJsonAsFile(props.result.json_content, props.result.json_filename)
    message.success(t('dataEngineering.result.downloaded', { filename: props.result.json_filename }))
  }
  catch (error) {
    message.error(t('dataEngineering.result.downloadJsonFailed'))
    console.error('下載失敗:', error)
  }
}
</script>

<template>
  <NCard :title="$t('dataEngineering.result.title')" class="result-card">
    <template #header-extra>
      <NTag v-if="result.from_cache" type="info" size="small">
        {{ $t('dataEngineering.result.fromCache') }}
      </NTag>
    </template>

    <!-- 法規資訊 -->
    <NDescriptions label-placement="left" :column="1" bordered class="mb-4">
      <NDescriptionsItem :label="$t('dataEngineering.result.pcodeLabel')">
        {{ result.pcode }}
      </NDescriptionsItem>
      <NDescriptionsItem :label="$t('dataEngineering.result.lawNameLabel')">
        {{ result.law_name }}
      </NDescriptionsItem>
      <NDescriptionsItem :label="$t('dataEngineering.result.chapters')">
        {{ result.statistics.chapters }}
      </NDescriptionsItem>
      <NDescriptionsItem :label="$t('dataEngineering.result.articles')">
        {{ result.statistics.articles }}
      </NDescriptionsItem>
      <NDescriptionsItem :label="$t('dataEngineering.result.items')">
        {{ result.statistics.items }}
      </NDescriptionsItem>
      <NDescriptionsItem :label="$t('dataEngineering.result.subitems')">
        {{ result.statistics.subitems }}
      </NDescriptionsItem>
      <NDescriptionsItem v-if="result.processing_time" :label="$t('dataEngineering.result.processingTime')">
        {{ result.processing_time.toFixed(2) }} {{ $t('dataEngineering.result.seconds') }}
      </NDescriptionsItem>
    </NDescriptions>

    <!-- 下載按鈕 -->
    <NSpace>
      <NButton type="primary" @click="handleDownloadMarkdown">
        <template #icon>
          <DownloadOutline />
        </template>
        {{ $t('dataEngineering.result.downloadMarkdown') }}
      </NButton>
      <NButton type="info" @click="handleDownloadJson">
        <template #icon>
          <DownloadOutline />
        </template>
        {{ $t('dataEngineering.result.downloadJson') }}
      </NButton>
    </NSpace>
  </NCard>
</template>

<style scoped>
.result-card {
  margin-top: 1.5rem;
}
</style>
