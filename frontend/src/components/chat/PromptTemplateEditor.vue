<script setup lang="ts">
import type { PromptTemplate, PromptTemplateCreateRequest, PromptTemplateUpdateRequest } from '@/types/prompt'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSpace,
  NSwitch,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'

interface Props {
  show: boolean
  template?: PromptTemplate | null
  loading?: boolean
}

interface Emits {
  (e: 'update:show', value: boolean): void
  (e: 'confirm', data: PromptTemplateCreateRequest | PromptTemplateUpdateRequest): void
}

const props = withDefaults(defineProps<Props>(), {
  template: null,
  loading: false,
})

const emit = defineEmits<Emits>()

// 表單資料
const formData = ref({
  name: '',
  content: '',
  description: '',
  is_favorite: false,
})

// 是否為編輯模式
const isEditMode = computed(() => !!props.template)

// Modal 標題
const modalTitle = computed(() => isEditMode.value ? '編輯提示詞模板' : '建立提示詞模板')

// 監聽 template 變化，更新表單資料
watch(() => props.template, (newTemplate) => {
  if (newTemplate) {
    formData.value = {
      name: newTemplate.name,
      content: newTemplate.content,
      description: newTemplate.description || '',
      is_favorite: newTemplate.is_favorite,
    }
  }
  else {
    resetForm()
  }
}, { immediate: true })

// 重置表單
function resetForm() {
  formData.value = {
    name: '',
    content: '',
    description: '',
    is_favorite: false,
  }
}

// 關閉 Modal
function handleClose() {
  emit('update:show', false)
  setTimeout(resetForm, 300)
}

// 確認提交
function handleConfirm() {
  // 驗證必填欄位
  if (!formData.value.name.trim()) {
    return
  }
  if (!formData.value.content.trim()) {
    return
  }

  const data = {
    name: formData.value.name.trim(),
    content: formData.value.content.trim(),
    description: formData.value.description.trim() || undefined,
    is_favorite: formData.value.is_favorite,
  }

  emit('confirm', data)
}
</script>

<template>
  <NModal
    :show="show"
    :mask-closable="false"
    preset="card"
    :title="modalTitle"
    class="prompt-template-editor-modal"
    :style="{ width: '680px' }"
    @update:show="handleClose"
  >
    <NForm
      :model="formData"
      label-placement="top"
      label-width="auto"
      require-mark-placement="right-hanging"
    >
      <NFormItem
        label="模板名稱"
        path="name"
        :show-feedback="false"
      >
        <NInput
          v-model:value="formData.name"
          placeholder="請輸入模板名稱（最多 100 字）"
          maxlength="100"
          show-count
          :disabled="loading"
        />
      </NFormItem>

      <NFormItem
        label="提示詞內容"
        path="content"
        :show-feedback="false"
      >
        <NInput
          v-model:value="formData.content"
          type="textarea"
          placeholder="請輸入提示詞內容（最多 5000 字）&#10;&#10;範例：&#10;你是一個專業的助手。請用繁體中文回答使用者的問題。"
          :rows="12"
          maxlength="5000"
          show-count
          :disabled="loading"
        />
      </NFormItem>

      <NFormItem
        label="描述（選填）"
        path="description"
        :show-feedback="false"
      >
        <NInput
          v-model:value="formData.description"
          type="textarea"
          placeholder="請輸入提示詞描述，說明此模板的用途"
          :rows="3"
          :disabled="loading"
        />
      </NFormItem>

      <NFormItem
        label="收藏此提示詞"
        path="is_favorite"
        :show-feedback="false"
      >
        <NSwitch
          v-model:value="formData.is_favorite"
          :disabled="loading"
        />
        <span class="ml-2 text-sm text-gray-500">
          開啟後，此提示詞將顯示收藏標記
        </span>
      </NFormItem>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton
          :disabled="loading"
          @click="handleClose"
        >
          取消
        </NButton>
        <NButton
          type="primary"
          :loading="loading"
          :disabled="!formData.name.trim() || !formData.content.trim()"
          @click="handleConfirm"
        >
          {{ isEditMode ? '更新' : '建立' }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.prompt-template-editor-modal {
  max-height: 85vh;
}

:deep(.n-card__content) {
  max-height: calc(85vh - 140px);
  overflow-y: auto;
}
</style>
