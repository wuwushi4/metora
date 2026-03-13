<script setup lang="ts">
import type { UploadFileInfo } from 'naive-ui'
import type { RegulationContent } from '@/types/regulation'
import { DocumentTextOutline as DocumentIcon } from '@vicons/ionicons5'
import {
  NButton,
  NIcon,
  NModal,
  NSpace,
  NText,
  NUpload,
  NUploadDragger,
} from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from '@/utils/message'

interface Props {
  show: boolean
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'upload': [content: RegulationContent]
}>()

const { t } = useI18n()

const fileList = ref<UploadFileInfo[]>([])
const uploading = ref(false)

// 監聽 show prop 變化，重置檔案列表
watch(() => props.show, (newShow) => {
  if (!newShow) {
    fileList.value = []
    uploading.value = false
  }
})

// 關閉彈窗
function handleClose() {
  if (!uploading.value) {
    emit('update:show', false)
  }
}

// 處理檔案變更
function handleFileChange(options: { fileList: UploadFileInfo[] }) {
  // 只保留最後一個檔案
  if (options.fileList.length > 1) {
    const lastFile = options.fileList[options.fileList.length - 1]
    if (lastFile) {
      fileList.value = [lastFile]
    }
  }
  else {
    fileList.value = options.fileList
  }
}

// 驗證 JSON 格式
async function validateJsonFile(file: File): Promise<RegulationContent | null> {
  try {
    const text = await file.text()
    const json = JSON.parse(text)

    // 驗證必要欄位
    if (!json.law_metadata || !json.chapters) {
      message.error(t('regulations.uploadModal.jsonMetadataError'))
      return null
    }

    // 驗證 law_metadata 結構
    const metadata = json.law_metadata

    // 支援舊版 pcode，但最終統一為 code
    const lawCode = metadata.code || metadata.pcode
    if (
      !metadata.name
      || !metadata.category
      || !metadata.status
      || !lawCode
      || !metadata.source_url
    ) {
      message.error(t('regulations.uploadModal.jsonFieldError'))
      return null
    }

    // 與舊資料相容：若只有 pcode，轉為 code
    if (!metadata.code && metadata.pcode) {
      metadata.code = metadata.pcode
    }
    delete metadata.pcode

    if (typeof metadata.source_url === 'string') {
      metadata.source_url = metadata.source_url.trim()
    }
    if (!metadata.source_url) {
      message.error(t('regulations.uploadModal.jsonSourceUrlEmpty'))
      return null
    }

    // 驗證 chapters 結構
    if (!Array.isArray(json.chapters)) {
      message.error(t('regulations.uploadModal.jsonChaptersArray'))
      return null
    }

    for (const chapter of json.chapters) {
      if (!chapter.chapter_num || !chapter.chapter_display || !chapter.articles) {
        message.error(t('regulations.uploadModal.jsonChapterStructure'))
        return null
      }

      // 確保 chapter_name 存在
      if (!chapter.chapter_name) {
        chapter.chapter_name = ''
      }

      if (!Array.isArray(chapter.articles)) {
        message.error(t('regulations.uploadModal.jsonArticlesArray'))
        return null
      }

      for (const article of chapter.articles) {
        if (!article.article_num || !article.article_display) {
          message.error(t('regulations.uploadModal.jsonArticleStructure'))
          return null
        }

        // 確保 content 欄位存在（Pydantic 驗證需要，即使為空字串）
        if (article.content === undefined || article.content === null) {
          article.content = ''
        }

        // scenarios 可選，但如果存在必須是陣列；如果不存在則初始化為空陣列
        if (!article.scenarios) {
          article.scenarios = []
        }
        else if (!Array.isArray(article.scenarios)) {
          message.error(t('regulations.uploadModal.jsonScenariosArray'))
          return null
        }

        // 保留完整的 JSON 結構，不刪除任何欄位（items, references, note, article_url 等）
      }
    }

    return json as RegulationContent
  }
  catch (error) {
    if (error instanceof SyntaxError) {
      message.error(t('regulations.uploadModal.jsonSyntaxError'))
    }
    else {
      message.error(t('regulations.uploadModal.readFailed'))
    }
    return null
  }
}

// 處理上傳
async function handleUpload() {
  if (fileList.value.length === 0) {
    message.warning(t('regulations.uploadModal.selectFile'))
    return
  }

  const fileInfo = fileList.value[0]
  if (!fileInfo || !fileInfo.file) {
    message.warning(t('regulations.uploadModal.noValidFiles'))
    return
  }

  uploading.value = true

  // 驗證 JSON 格式
  const content = await validateJsonFile(fileInfo.file)
  if (!content) {
    uploading.value = false
    return
  }

  // 傳送內容給父組件處理
  emit('upload', content)
  uploading.value = false
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
    :mask-closable="!uploading"
    preset="card"
    :title="$t('regulations.uploadModal.title')"
    style="width: 600px"
    @update:show="handleClose"
  >
    <div class="upload-container">
      <NUpload
        v-model:file-list="fileList"
        :default-upload="false"
        accept=".json"
        :max="1"
        @change="handleFileChange"
        @remove="handleRemove"
      >
        <NUploadDragger>
          <div class="upload-dragger-content">
            <div class="upload-icon">
              <NIcon size="48" :depth="3">
                <DocumentIcon />
              </NIcon>
            </div>
            <NText class="upload-text">
              {{ $t('regulations.uploadModal.dragText') }}
            </NText>
            <NText class="upload-hint" depth="3">
              {{ $t('regulations.uploadModal.onlyJson') }}
            </NText>
            <NText class="upload-hint" depth="3">
              {{ $t('regulations.uploadModal.singleFile') }}
            </NText>
          </div>
        </NUploadDragger>
      </NUpload>

      <div class="upload-tips">
        <div class="tip-item">
          <span class="tip-icon">📋</span>
          <span class="tip-text">{{ $t('regulations.uploadModal.tipRequired') }}</span>
        </div>
        <div class="tip-item">
          <span class="tip-icon">✅</span>
          <span class="tip-text">{{ $t('regulations.uploadModal.tipValidate') }}</span>
        </div>
        <div class="tip-item">
          <span class="tip-icon">💡</span>
          <span class="tip-text">{{ $t('regulations.uploadModal.tipDuplicate') }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <NSpace justify="end">
        <NButton :disabled="uploading" @click="handleClose">
          {{ $t('common.actions.cancel') }}
        </NButton>
        <NButton
          type="primary"
          :disabled="fileList.length === 0"
          :loading="uploading"
          @click="handleUpload"
        >
          {{ $t('common.actions.upload') }}
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
