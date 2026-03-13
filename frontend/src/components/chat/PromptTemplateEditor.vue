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
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
const modalTitle = computed(() => isEditMode.value ? t('chat.prompts.editor.editTitle') : t('chat.prompts.editor.createTitle'))

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
        :label="$t('chat.prompts.editor.nameLabel')"
        path="name"
        :show-feedback="false"
      >
        <NInput
          v-model:value="formData.name"
          :placeholder="$t('chat.prompts.editor.namePlaceholder')"
          maxlength="100"
          show-count
          :disabled="loading"
        />
      </NFormItem>

      <NFormItem
        :label="$t('chat.prompts.editor.contentLabel')"
        path="content"
        :show-feedback="false"
      >
        <NInput
          v-model:value="formData.content"
          type="textarea"
          :placeholder="$t('chat.prompts.editor.contentPlaceholder')"
          :rows="12"
          maxlength="5000"
          show-count
          :disabled="loading"
        />
      </NFormItem>

      <NFormItem
        :label="$t('chat.prompts.editor.descLabel')"
        path="description"
        :show-feedback="false"
      >
        <NInput
          v-model:value="formData.description"
          type="textarea"
          :placeholder="$t('chat.prompts.editor.descPlaceholder')"
          :rows="3"
          :disabled="loading"
        />
      </NFormItem>

      <NFormItem
        :label="$t('chat.prompts.editor.favoriteLabel')"
        path="is_favorite"
        :show-feedback="false"
      >
        <NSwitch
          v-model:value="formData.is_favorite"
          :disabled="loading"
        />
        <span class="ml-2 text-sm text-gray-500">
          {{ $t('chat.prompts.editor.favoriteHint') }}
        </span>
      </NFormItem>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton
          :disabled="loading"
          @click="handleClose"
        >
          {{ $t('common.actions.cancel') }}
        </NButton>
        <NButton
          type="primary"
          :loading="loading"
          :disabled="!formData.name.trim() || !formData.content.trim()"
          @click="handleConfirm"
        >
          {{ isEditMode ? $t('common.actions.update') : $t('common.actions.create') }}
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
