<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import type { Collection, CollectionCreateRequest, CollectionUpdateRequest } from '@/types/collection'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSelect,
  NSpace,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from '@/utils/message'

const { t } = useI18n()

interface Props {
  show: boolean
  mode: 'create' | 'edit'
  collection?: Collection | null
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  mode: 'create',
  collection: null,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: CollectionCreateRequest | CollectionUpdateRequest]
}>()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

// 表單資料 - 新增模式
const formData = ref<CollectionCreateRequest>({
  name: '',
  description: '',
  chunking_strategy: 'qa_multi_representation',
})

// 表單資料 - 編輯模式
const editFormData = ref<CollectionUpdateRequest>({
  name: '',
  description: '',
})

// 分塊策略選項
const chunkingStrategyOptions = computed(() => [
  { label: t('collections.form.strategies.qa_multi_representation'), value: 'qa_multi_representation' },
  { label: t('collections.form.strategies.regulation_hierarchical'), value: 'regulation_hierarchical' },
  { label: t('collections.form.strategies.regulation_scenario_description'), value: 'regulation_manual_scenario' },
  { label: t('collections.form.strategies.recursive_text'), value: 'recursive_text' },
])

// 表單標題
const title = computed(() => {
  return props.mode === 'create' ? t('collections.form.createTitle') : t('collections.form.editTitle')
})

// 驗證規則 - 新增模式
const createRules = computed<FormRules>(() => ({
  name: [
    { required: true, message: t('collections.form.namePlaceholder'), trigger: 'blur' },
    { min: 1, max: 100, message: t('users.form.usernameLength'), trigger: 'blur' },
  ],
  chunking_strategy: [
    { required: true, message: t('collections.form.chunkingPlaceholder'), trigger: 'change' },
  ],
}))

// 驗證規則 - 編輯模式
const editRules = computed<FormRules>(() => ({
  name: [
    { required: true, message: t('collections.form.namePlaceholder'), trigger: 'blur' },
    { min: 1, max: 100, message: t('users.form.usernameLength'), trigger: 'blur' },
  ],
}))

// 當前驗證規則
const rules = computed(() => {
  return props.mode === 'create' ? createRules.value : editRules.value
})

// 監聽 collection prop 變化，更新表單資料
watch(() => props.collection, (newCollection) => {
  if (newCollection && props.mode === 'edit') {
    editFormData.value = {
      name: newCollection.name,
      description: newCollection.description || '',
    }
  }
}, { immediate: true })

// 監聽 show prop 變化，重置表單
watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
  else if (newShow && props.mode === 'create') {
    // 新增模式時重置為預設值
    formData.value = {
      name: '',
      description: '',
      chunking_strategy: 'qa_multi_representation',
    }
  }
})

// 重置表單
function resetForm() {
  formRef.value?.restoreValidation()
}

// 關閉彈窗
function handleClose() {
  emit('update:show', false)
}

// 提交表單
async function handleSubmit() {
  try {
    await formRef.value?.validate()

    loading.value = true

    if (props.mode === 'create') {
      emit('submit', formData.value)
    }
    else {
      emit('submit', editFormData.value)
    }
  }
  catch (error: any) {
    console.error('表單驗證失敗:', error)
    message.error(t('collections.form.validationFailed'))
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <NModal
    :show="show"
    :mask-closable="false"
    preset="card"
    :title="title"
    style="width: 600px"
    @update:show="handleClose"
  >
    <NForm
      ref="formRef"
      :model="mode === 'create' ? formData : editFormData"
      :rules="rules"
      label-placement="left"
      label-width="100px"
      require-mark-placement="right-hanging"
    >
      <!-- 新增模式 -->
      <template v-if="mode === 'create'">
        <NFormItem path="name" :label="$t('collections.form.nameLabel')">
          <NInput
            v-model:value="formData.name"
            :placeholder="$t('collections.form.namePlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="description" :label="$t('common.fields.description')">
          <NInput
            v-model:value="formData.description"
            type="textarea"
            :placeholder="$t('collections.form.descPlaceholder')"
            :rows="3"
            clearable
          />
        </NFormItem>

        <NFormItem path="chunking_strategy" :label="$t('collections.form.chunkingStrategy')">
          <NSelect
            v-model:value="formData.chunking_strategy"
            :options="chunkingStrategyOptions"
            :placeholder="$t('collections.form.chunkingPlaceholder')"
          />
        </NFormItem>

        <div class="form-tip">
          <p class="tip-text">
            {{ $t('collections.form.tipCreate') }}
          </p>
        </div>
      </template>

      <!-- 編輯模式 -->
      <template v-else>
        <NFormItem path="name" :label="$t('collections.form.nameLabel')">
          <NInput
            v-model:value="editFormData.name"
            :placeholder="$t('collections.form.namePlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="description" :label="$t('common.fields.description')">
          <NInput
            v-model:value="editFormData.description"
            type="textarea"
            :placeholder="$t('collections.form.descPlaceholder')"
            :rows="3"
            clearable
          />
        </NFormItem>

        <NFormItem :label="$t('collections.form.chunkingStrategy')">
          <NInput :value="collection?.chunking_strategy" disabled />
        </NFormItem>

        <div class="form-tip">
          <p class="tip-text">
            {{ $t('collections.form.tipEdit') }}
          </p>
        </div>
      </template>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">
          {{ $t('common.actions.cancel') }}
        </NButton>
        <NButton type="primary" :loading="loading" @click="handleSubmit">
          {{ mode === 'create' ? $t('common.actions.create') : $t('common.actions.save') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.form-tip {
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  border-radius: 6px;
}

.tip-text {
  margin: 0;
  font-size: 0.875rem;
  color: #0369a1;
  line-height: 1.5;
  white-space: pre-line;
}
</style>
