<script setup lang="ts">
import type { FilePreview as FilePreviewType } from '@/types/upload'
import { AttachOutline, StopCircleOutline } from '@vicons/ionicons5'
import { NButton, NIcon, NInput, NSpace } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chat'

const { t } = useI18n()
import {
  createFilePreview,
  DEFAULT_FILE_RULES,
  validateFiles,
} from '@/utils/fileUtils'
import { message } from '@/utils/message'
import FilePreview from './FilePreview.vue'

interface Props {
  disabled?: boolean
  loading?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  loading: false,
  placeholder: undefined,
})

const emit = defineEmits<Emits>()

interface Emits {
  (e: 'send', content: string, files: File[]): void
  (e: 'stop'): void
}

const chatStore = useChatStore()

const inputValue = ref('')
const inputRef = ref<InstanceType<typeof NInput> | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

// 計算是否可以發送
const canSend = computed(() => {
  const hasContent = inputValue.value.trim().length > 0
  const hasFiles = chatStore.pendingFiles.length > 0
  return (hasContent || hasFiles) && !props.disabled && !props.loading
})

// 檔案數量資訊
const fileCountInfo = computed(() => {
  const current = chatStore.pendingFiles.length
  const max = DEFAULT_FILE_RULES.maxFiles
  return {
    current,
    max,
    remaining: max - current,
    isMax: current >= max,
  }
})

// 處理發送
function handleSend() {
  if (!canSend.value) {
    return
  }

  const content = inputValue.value.trim()
  const files = chatStore.pendingFiles.map(f => f.file)

  emit('send', content, files)

  // 清空輸入框和附件
  inputValue.value = ''
  chatStore.clearPendingFiles()

  // 重新聚焦
  focusInput()
}

// 處理停止
function handleStop() {
  emit('stop')
}

// 處理鍵盤事件
function handleKeydown(event: KeyboardEvent) {
  // Enter 發送,Shift + Enter 換行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

// 處理檔案選擇
function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])

  if (files.length === 0)
    return

  // 檢查總數是否超過限制
  const currentCount = chatStore.pendingFiles.length
  const newCount = currentCount + files.length
  const maxFiles = DEFAULT_FILE_RULES.maxFiles

  if (newCount > maxFiles) {
    message.error(t('chat.input.maxFiles', { max: maxFiles, current: currentCount }))
    input.value = '' // 清空 input
    return
  }

  // 驗證檔案
  const error = validateFiles(files, DEFAULT_FILE_RULES)
  if (error) {
    message.error(error.message)
    input.value = '' // 清空 input
    return
  }

  // 創建預覽
  const previews: FilePreviewType[] = files.map(file => createFilePreview(file))
  chatStore.addPendingFiles(previews)

  // 清空 input 以允許重複選擇同一檔案
  input.value = ''
}

// 打開檔案選擇對話框
function openFileDialog() {
  fileInputRef.value?.click()
}

// 移除附件
function handleRemoveFile(fileId: string) {
  chatStore.removePendingFile(fileId)
}

// 處理拖放
function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false

  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length === 0)
    return

  // 檢查總數是否超過限制
  const currentCount = chatStore.pendingFiles.length
  const newCount = currentCount + files.length
  const maxFiles = DEFAULT_FILE_RULES.maxFiles

  if (newCount > maxFiles) {
    message.error(t('chat.input.maxFiles', { max: maxFiles, current: currentCount }))
    return
  }

  // 驗證檔案
  const error = validateFiles(files, DEFAULT_FILE_RULES)
  if (error) {
    message.error(error.message)
    return
  }

  // 創建預覽
  const previews: FilePreviewType[] = files.map(file => createFilePreview(file))
  chatStore.addPendingFiles(previews)
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave(event: DragEvent) {
  // 避免在子元素上觸發
  const target = event.currentTarget as HTMLElement
  const related = event.relatedTarget as HTMLElement

  if (!target.contains(related)) {
    isDragging.value = false
  }
}

// 聚焦輸入框
function focusInput() {
  inputRef.value?.focus()
}

// 當 loading 狀態變為 false 時,自動聚焦
watch(() => props.loading, (newLoading, oldLoading) => {
  if (oldLoading && !newLoading) {
    setTimeout(() => {
      focusInput()
    }, 100)
  }
})

// 暴露方法給父組件
defineExpose({
  focusInput,
})
</script>

<template>
  <div
    class="message-input-container" :class="[{ 'is-dragging': isDragging }]"
    :data-drop-hint="$t('chat.input.dropHint')"
    @drop="handleDrop"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
  >
    <!-- 附件預覽區 -->
    <div
      v-if="chatStore.hasPendingFiles"
      class="files-preview-area"
    >
      <FilePreview
        v-for="file in chatStore.pendingFiles"
        :key="file.id"
        :file="file"
        @remove="handleRemoveFile"
      />
    </div>

    <!-- 輸入框 -->
    <div class="input-wrapper">
      <NInput
        ref="inputRef"
        v-model:value="inputValue"
        type="textarea"
        :placeholder="placeholder || t('chat.input.placeholder')"
        :disabled="disabled || loading"
        :autosize="{
          minRows: 1,
          maxRows: 6,
        }"
        :maxlength="2000"
        show-count
        clearable
        @keydown="handleKeydown"
      />
    </div>

    <!-- 按鈕區 -->
    <div class="button-wrapper">
      <NSpace :size="12" justify="space-between" style="width: 100%">
        <!-- 附件按鈕 -->
        <div class="left-buttons">
          <NButton
            text
            :disabled="disabled || loading || fileCountInfo.isMax"
            @click="openFileDialog"
          >
            <template #icon>
              <NIcon size="20">
                <AttachOutline />
              </NIcon>
            </template>
            {{ $t('chat.input.uploadFile') }}
            <span
              v-if="fileCountInfo.current > 0"
              :style="{ color: fileCountInfo.isMax ? '#ef4444' : '#6b7280', marginLeft: '4px' }"
            >
              ({{ fileCountInfo.current }} / {{ fileCountInfo.max }})
            </span>
          </NButton>

          <!-- 隱藏的檔案輸入 -->
          <input
            ref="fileInputRef"
            type="file"
            multiple
            accept="image/*,application/pdf,.xlsx,.xls,.csv,.docx"
            style="display: none"
            @change="handleFileSelect"
          >
        </div>

        <!-- 發送/停止按鈕 -->
        <NButton
          v-if="!loading"
          type="primary"
          :disabled="!canSend"
          @click="handleSend"
        >
          {{ $t('chat.input.send') }}
        </NButton>
        <NButton
          v-else
          type="error"
          @click="handleStop"
        >
          <template #icon>
            <NIcon size="18">
              <StopCircleOutline />
            </NIcon>
          </template>
          {{ $t('chat.input.stop') }}
        </NButton>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.message-input-container {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 拖拽狀態遮罩 */
.message-input-container.is-dragging::before {
  content: attr(data-drop-hint);
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(14, 165, 233, 0.1);
  border: 2px dashed rgba(14, 165, 233, 0.5);
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #0ea5e9;
  z-index: 10;
  pointer-events: none;
  backdrop-filter: blur(4px);
}

.files-preview-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.input-wrapper {
  flex: 1;
}

.button-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 自訂輸入框樣式 */
:deep(.n-input) {
  --n-border-radius: 10px;
  --n-font-size: 0.9375rem;
  border: 1.5px solid transparent;
  background-image:
    linear-gradient(rgba(255, 255, 255, 1), rgba(255, 255, 255, 1)),
    linear-gradient(135deg, rgba(229, 231, 235, 0.8) 0%, rgba(203, 213, 225, 0.6) 100%);
  background-origin: padding-box, border-box;
  background-clip: padding-box, border-box;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.04),
    inset 0 1px 3px rgba(0, 0, 0, 0.02),
    inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.n-input:hover) {
  background-image:
    linear-gradient(rgba(255, 255, 255, 1), rgba(255, 255, 255, 1)),
    linear-gradient(135deg, rgba(14, 165, 233, 0.3) 0%, rgba(99, 102, 241, 0.3) 50%, rgba(139, 92, 246, 0.3) 100%);
  box-shadow:
    0 4px 8px rgba(14, 165, 233, 0.08),
    0 2px 4px rgba(139, 92, 246, 0.06),
    inset 0 1px 3px rgba(0, 0, 0, 0.02),
    inset 0 0 0 1px rgba(255, 255, 255, 0.6);
}

:deep(.n-input.n-input--focus) {
  background-image:
    linear-gradient(rgba(255, 255, 255, 1), rgba(255, 255, 255, 1)),
    linear-gradient(135deg, rgba(14, 165, 233, 0.5) 0%, rgba(99, 102, 241, 0.5) 50%, rgba(139, 92, 246, 0.5) 100%);
  box-shadow:
    0 0 0 4px rgba(14, 165, 233, 0.1),
    0 0 0 2px rgba(99, 102, 241, 0.08),
    0 6px 16px rgba(14, 165, 233, 0.15),
    0 3px 8px rgba(139, 92, 246, 0.12),
    inset 0 1px 3px rgba(0, 0, 0, 0.02),
    inset 0 0 0 1px rgba(255, 255, 255, 0.8);
}

:deep(.n-input__textarea-el) {
  line-height: 1.6;
  resize: none;
}

:deep(.n-input--textarea) {
  padding: 12px 16px;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .message-input-container {
    padding: 12px 16px;
    gap: 10px;
  }

  :deep(.n-input) {
    --n-font-size: 0.875rem;
  }
}
</style>
