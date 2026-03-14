<script setup lang="ts">
import type { ToolOutputFile, ToolResultRecord } from '@/types/chat'
import { computed } from 'vue'
import { NButton, NCard, NImage, NTag, NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'

interface Props {
  toolResults: ToolResultRecord[]
}

const props = defineProps<Props>()

const { t } = useI18n()

interface DisplayOutputFile extends ToolOutputFile {
  tool_name: string
  data_url: string
}

const outputFiles = computed<DisplayOutputFile[]>(() => {
  return props.toolResults.flatMap((result) => {
    const files = Array.isArray(result.output_files) ? result.output_files : []

    return files.map(file => ({
      ...file,
      tool_name: result.tool_name,
      data_url: `data:${file.mime_type};base64,${file.content_base64}`,
    }))
  })
})

function isImage(file: DisplayOutputFile): boolean {
  return file.mime_type.startsWith('image/')
}

function downloadFile(file: DisplayOutputFile) {
  const link = document.createElement('a')
  link.href = file.data_url
  link.download = file.filename
  link.click()
}

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(2)} MB`
}
</script>

<template>
  <div v-if="outputFiles.length > 0" class="tool-output-files">
    <div class="section-title">
      <NText strong>{{ t('chat.toolOutput.title') }}</NText>
    </div>

    <div class="output-grid">
      <NCard
        v-for="file in outputFiles"
        :key="`${file.tool_name}-${file.filename}`"
        size="small"
        class="output-card"
      >
        <template #header>
          <div class="output-header">
            <NTag size="small" :bordered="false" type="info">
              {{ file.tool_name }}
            </NTag>
            <NText class="output-filename">
              {{ file.filename }}
            </NText>
          </div>
        </template>

        <div v-if="isImage(file)" class="image-wrapper">
          <NImage
            :src="file.data_url"
            :alt="file.filename"
            object-fit="contain"
            class="output-image"
            :preview-src="file.data_url"
          />
        </div>

        <div v-else class="file-actions">
          <NButton size="small" secondary @click="downloadFile(file)">
            {{ t('chat.toolOutput.downloadFile') }}
          </NButton>
        </div>

        <div class="output-footer">
          <NText depth="3" class="file-meta">
            {{ file.mime_type }} · {{ formatFileSize(file.size) }}
          </NText>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.tool-output-files {
  margin-top: 16px;
}

.section-title {
  margin-bottom: 10px;
}

.output-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.output-card {
  background: linear-gradient(135deg, #fafafa 0%, #f5f7fb 100%);
}

.output-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.output-filename {
  font-size: 0.875rem;
  word-break: break-word;
}

.image-wrapper {
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.output-image {
  width: 100%;
  max-height: 320px;
}

.file-actions {
  display: flex;
  justify-content: flex-start;
}

.output-footer {
  margin-top: 10px;
}

.file-meta {
  font-size: 0.75rem;
}
</style>
