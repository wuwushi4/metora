<script setup lang="ts">
import type { UploadFileInfo } from 'naive-ui'
import { CloudUploadOutline as UploadIcon } from '@vicons/ionicons5'
import {
  NButton,
  NCard,
  NIcon,
  NInputNumber,
  NModal,
  NSpace,
  NText,
  NUpload,
  NUploadDragger,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getChunkingDefaults } from '@/api/datasets'
import { message } from '@/utils/message'

interface Props {
  show: boolean
  collectionId: number
  chunkingStrategy: string
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  chunkingStrategy: '',
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'upload': [files: File[], chunkingOptions?: { chunkSize: number, chunkOverlap: number }]
}>()

const { t } = useI18n()

const fileList = ref<UploadFileInfo[]>([])

// 分塊參數
const chunkSize = ref<number | null>(1000)
const chunkOverlap = ref<number | null>(200)
const loadingDefaults = ref(false)

const strategyFileTypeMap: Record<string, string[]> = {
  qa_multi_representation: ['.json'],
  regulation_hierarchical: ['.json'],
  regulation_context_enriched: ['.json'],
  regulation_manual_scenario: ['.json'],
  recursive_text: ['.pdf', '.txt', '.md'],
}

const isRecursiveText = computed(() => props.chunkingStrategy === 'recursive_text')

// 依 Collection 的分塊策略動態決定可接受的檔案類型
const acceptedFileTypes = computed<string[]>(() => {
  const mapped = props.chunkingStrategy
    ? strategyFileTypeMap[props.chunkingStrategy]
    : undefined
  return mapped ?? ['.json', '.pdf', '.txt', '.md']
})

// 載入系統預設分塊參數
async function loadChunkingDefaults() {
  loadingDefaults.value = true
  try {
    const defaults = await getChunkingDefaults()
    chunkSize.value = defaults.chunk_size
    chunkOverlap.value = defaults.chunk_overlap
  }
  catch (error: any) {
    console.error('載入分塊預設參數失敗:', error)
  }
  finally {
    loadingDefaults.value = false
  }
}

// 監聽 show prop 變化，重置檔案列表並載入預設值
watch(() => props.show, (newShow) => {
  if (!newShow) {
    fileList.value = []
  }
  else if (newShow && isRecursiveText.value) {
    loadChunkingDefaults()
  }
})

// 關閉彈窗
function handleClose() {
  emit('update:show', false)
}

// 處理檔案變更
function handleFileChange(options: { fileList: UploadFileInfo[] }) {
  fileList.value = options.fileList
}

// 處理上傳（將檔案傳遞給父組件）
function handleUpload() {
  if (fileList.value.length === 0) {
    message.warning(t('collections.dataset.uploadModal.noFiles'))
    return
  }

  // 將檔案資訊傳遞給父組件
  const files = fileList.value
    .filter(file => file.file)
    .map(file => file.file!)

  if (files.length === 0) {
    message.warning(t('collections.dataset.uploadModal.noValidFiles'))
    return
  }

  if (isRecursiveText.value && chunkSize.value && chunkOverlap.value != null) {
    emit('upload', files, {
      chunkSize: chunkSize.value,
      chunkOverlap: chunkOverlap.value,
    })
  }
  else {
    emit('upload', files)
  }
}

// 移除檔案
function handleRemove(options: { file: UploadFileInfo, fileList: UploadFileInfo[] }) {
  fileList.value = options.fileList
  return true
}
</script>

<template>
  <NModal
    :show="show"
    :mask-closable="false"
    preset="card"
    :title="$t('collections.dataset.uploadModal.title')"
    style="width: 600px"
    @update:show="handleClose"
  >
    <div class="upload-container">
      <NUpload
        v-model:file-list="fileList"
        :default-upload="false"
        :accept="acceptedFileTypes.join(',')"
        :max="10"
        multiple
        directory-dnd
        @change="handleFileChange"
        @remove="handleRemove"
      >
        <NUploadDragger>
          <div class="upload-dragger-content">
            <div class="upload-icon">
              <NIcon size="48" :depth="3">
                <UploadIcon />
              </NIcon>
            </div>
            <NText class="upload-text">
              {{ $t('collections.dataset.uploadModal.dragText') }}
            </NText>
            <NText class="upload-hint" depth="3">
              {{ $t('collections.dataset.uploadModal.supportedTypes', { types: acceptedFileTypes.join(', ') }) }}
            </NText>
            <NText class="upload-hint" depth="3">
              {{ $t('collections.dataset.uploadModal.maxFiles') }}
            </NText>
          </div>
        </NUploadDragger>
      </NUpload>

      <!-- 遞迴分塊參數設定（僅 recursive_text 策略顯示） -->
      <NCard v-if="isRecursiveText" :title="$t('collections.dataset.uploadModal.chunkParams')" size="small" class="chunking-config">
        <div class="config-fields">
          <div class="config-field">
            <label class="config-label">{{ $t('collections.dataset.uploadModal.chunkSizeLabel') }}</label>
            <NInputNumber
              v-model:value="chunkSize"
              :min="50"
              :max="10000"
              :step="100"
              :loading="loadingDefaults"
              :placeholder="$t('collections.dataset.uploadModal.chunkSizePlaceholder')"
              style="width: 100%"
            />
            <span class="config-hint">{{ $t('collections.dataset.uploadModal.chunkSizeHint') }}</span>
          </div>
          <div class="config-field">
            <label class="config-label">{{ $t('collections.dataset.uploadModal.overlapLabel') }}</label>
            <NInputNumber
              v-model:value="chunkOverlap"
              :min="0"
              :max="5000"
              :step="50"
              :loading="loadingDefaults"
              :placeholder="$t('collections.dataset.uploadModal.overlapPlaceholder')"
              style="width: 100%"
            />
            <span class="config-hint">{{ $t('collections.dataset.uploadModal.overlapHint') }}</span>
          </div>
        </div>
        <div class="config-tip">
          {{ $t('collections.dataset.uploadModal.defaultParamsHint') }}
        </div>
      </NCard>

      <div class="upload-tips">
        <div class="tip-item">
          <span class="tip-icon">💡</span>
          <span class="tip-text">{{ $t('collections.dataset.uploadModal.tipAutoProcess') }}</span>
        </div>
        <div class="tip-item">
          <span class="tip-icon">⚠️</span>
          <span class="tip-text">{{ $t('collections.dataset.uploadModal.tipLargeFile') }}</span>
        </div>
        <div class="tip-item">
          <span class="tip-icon">🔄</span>
          <span class="tip-text">{{ $t('collections.dataset.uploadModal.tipRefresh') }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">
          {{ $t('common.actions.cancel') }}
        </NButton>
        <NButton
          type="primary"
          :disabled="fileList.length === 0"
          @click="handleUpload"
        >
          {{ $t('collections.dataset.uploadModal.startUpload') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-dragger-content {
  padding: 40px 20px;
  text-align: center;
}

.upload-icon {
  margin-bottom: 12px;
  color: #0ea5e9;
}

.upload-text {
  display: block;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 8px;
}

.upload-hint {
  display: block;
  font-size: 0.875rem;
  margin-top: 4px;
}

.chunking-config {
  border: 1px solid #e0f2fe;
  background: #f0f9ff;
}

.config-fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.config-hint {
  font-size: 0.75rem;
  color: #9ca3af;
}

.config-tip {
  margin-top: 12px;
  padding: 8px 12px;
  font-size: 0.8rem;
  color: #0369a1;
  background: #e0f2fe;
  border-radius: 4px;
}

.upload-tips {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 0.875rem;
  color: #6b7280;
}

.tip-item:last-child {
  margin-bottom: 0;
}

.tip-icon {
  flex-shrink: 0;
  font-size: 1rem;
}

.tip-text {
  flex: 1;
  line-height: 1.5;
}
</style>
