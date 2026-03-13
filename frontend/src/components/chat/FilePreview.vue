<script setup lang="ts">
import type { FilePreview } from '@/types/upload'
import { CloseCircleOutline, DocumentTextOutline, GridOutline } from '@vicons/ionicons5'
import { NButton, NCard, NIcon, NImage, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { formatFileSize } from '@/utils/fileUtils'

const { t } = useI18n()

interface Props {
  file: FilePreview
}

interface Emits {
  (e: 'remove', fileId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

function handleRemove() {
  emit('remove', props.file.id)
}

function getStatusText() {
  switch (props.file.status) {
    case 'pending':
      return t('chat.filePreview.pending')
    case 'uploading':
      return t('chat.filePreview.uploading')
    case 'success':
      return t('chat.filePreview.success')
    case 'error':
      return props.file.error || t('chat.filePreview.failed')
    default:
      return ''
  }
}

function getStatusColor() {
  switch (props.file.status) {
    case 'pending':
      return '#666'
    case 'uploading':
      return '#18a058'
    case 'success':
      return '#18a058'
    case 'error':
      return '#d03050'
    default:
      return '#666'
  }
}
</script>

<template>
  <NCard
    class="file-preview-card"
    :bordered="true"
    size="small"
  >
    <div class="file-preview-content">
      <!-- 檔案預覽 -->
      <div class="preview-image-container">
        <!-- 圖片預覽 -->
        <NImage
          v-if="file.type === 'image'"
          :src="file.previewUrl"
          :alt="file.file.name"
          object-fit="cover"
          class="preview-image"
          :preview-disabled="false"
        />

        <!-- PDF 預覽 -->
        <div
          v-else-if="file.type === 'pdf_page'"
          class="pdf-preview"
        >
          <NIcon :size="32" color="#d03050">
            <DocumentTextOutline />
          </NIcon>
          <span class="pdf-label">PDF</span>
        </div>

        <!-- 試算表/檔案預覽 -->
        <div
          v-else-if="file.type === 'file'"
          class="file-type-preview"
        >
          <NIcon :size="32" color="#18a058">
            <GridOutline />
          </NIcon>
          <span class="file-type-label">{{ file.file.name.split('.').pop()?.toUpperCase() }}</span>
        </div>

        <!-- 上傳中遮罩 -->
        <div
          v-if="file.status === 'uploading'"
          class="uploading-overlay"
        >
          <NSpin size="small" />
        </div>

        <!-- 錯誤遮罩 -->
        <div
          v-if="file.status === 'error'"
          class="error-overlay"
        >
          <span class="error-icon">✕</span>
        </div>
      </div>

      <!-- 檔案資訊 -->
      <div class="file-info">
        <div class="file-name" :title="file.file.name">
          {{ file.file.name }}
        </div>
        <div class="file-meta">
          <span class="file-size">{{ formatFileSize(file.file.size) }}</span>
          <span
            class="file-status"
            :style="{ color: getStatusColor() }"
          >
            {{ getStatusText() }}
          </span>
        </div>
      </div>

      <!-- 刪除按鈕 -->
      <div class="remove-button">
        <NButton
          text
          type="error"
          size="small"
          :disabled="file.status === 'uploading'"
          @click="handleRemove"
        >
          <template #icon>
            <NIcon size="18">
              <CloseCircleOutline />
            </NIcon>
          </template>
        </NButton>
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.file-preview-card {
  margin-bottom: 8px;
}

.file-preview-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-image-container {
  position: relative;
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f5f5;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.pdf-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.pdf-label {
  font-size: 10px;
  font-weight: 600;
  color: #d03050;
  letter-spacing: 0.5px;
}

.file-type-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.file-type-label {
  font-size: 10px;
  font-weight: 600;
  color: #18a058;
  letter-spacing: 0.5px;
}

.uploading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.error-overlay {
  background: rgba(208, 48, 80, 0.8);
}

.error-icon {
  color: white;
  font-size: 24px;
  font-weight: bold;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.file-size {
  color: #999;
}

.file-status {
  font-weight: 500;
}

.remove-button {
  flex-shrink: 0;
}
</style>
