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
import { message } from '@/utils/message'

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
const chunkingStrategyOptions = [
  { label: 'QA 多重表徵 - 適用於問答對資料（JSON）', value: 'qa_multi_representation' },
  { label: '法規-階層式 - 使用完整法規結構（JSON）', value: 'regulation_hierarchical' },
  // { label: '法規情境增強 - 自動生成情境描述（使用 LLM）', value: 'regulation_context_enriched' },
  { label: '法規-情境描述 - 法規結構與情境描述 HyDE（JSON）', value: 'regulation_manual_scenario' },
  { label: '遞迴文字分塊 - 適用於 PDF、TXT、Markdown', value: 'recursive_text' },
]

// 表單標題
const title = computed(() => {
  return props.mode === 'create' ? '新增 Collection' : '編輯 Collection'
})

// 驗證規則 - 新增模式
const createRules: FormRules = {
  name: [
    { required: true, message: '請輸入 Collection 名稱', trigger: 'blur' },
    { min: 1, max: 100, message: '長度在 1 到 100 個字元', trigger: 'blur' },
  ],
  chunking_strategy: [
    { required: true, message: '請選擇分塊策略', trigger: 'change' },
  ],
}

// 驗證規則 - 編輯模式
const editRules: FormRules = {
  name: [
    { required: true, message: '請輸入 Collection 名稱', trigger: 'blur' },
    { min: 1, max: 100, message: '長度在 1 到 100 個字元', trigger: 'blur' },
  ],
}

// 當前驗證規則
const rules = computed(() => {
  return props.mode === 'create' ? createRules : editRules
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
    message.error('請檢查表單欄位')
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
        <NFormItem path="name" label="Collection 名稱">
          <NInput
            v-model:value="formData.name"
            placeholder="請輸入 Collection 名稱"
            clearable
          />
        </NFormItem>

        <NFormItem path="description" label="描述">
          <NInput
            v-model:value="formData.description"
            type="textarea"
            placeholder="請輸入 Collection 描述（可選）"
            :rows="3"
            clearable
          />
        </NFormItem>

        <NFormItem path="chunking_strategy" label="分塊策略">
          <NSelect
            v-model:value="formData.chunking_strategy"
            :options="chunkingStrategyOptions"
            placeholder="請選擇分塊策略"
          />
        </NFormItem>

        <div class="form-tip">
          <p class="tip-text">
            💡 提示：分塊策略在建立後無法修改。請根據資料類型選擇：<br>
            • QA 多重表徵：適用於問答對格式的 JSON 資料<br>
            • 法規-階層式：適用於法規 JSON，使用完整法規結構<br>
            <!-- • 法規情境增強：適用於法規 JSON，使用 LLM 自動生成情境描述<br> -->
            • 法規-情境描述：適用於法規 JSON，法規結構與情境描述（HyDE）<br>
            • 遞迴文字分塊：適用於 PDF、TXT、Markdown 等非結構化文件
          </p>
        </div>
      </template>

      <!-- 編輯模式 -->
      <template v-else>
        <NFormItem path="name" label="Collection 名稱">
          <NInput
            v-model:value="editFormData.name"
            placeholder="請輸入 Collection 名稱"
            clearable
          />
        </NFormItem>

        <NFormItem path="description" label="描述">
          <NInput
            v-model:value="editFormData.description"
            type="textarea"
            placeholder="請輸入 Collection 描述（可選）"
            :rows="3"
            clearable
          />
        </NFormItem>

        <NFormItem label="分塊策略">
          <NInput :value="collection?.chunking_strategy" disabled />
        </NFormItem>

        <div class="form-tip">
          <p class="tip-text">
            💡 提示：分塊策略建立後無法修改。
          </p>
        </div>
      </template>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">
          取消
        </NButton>
        <NButton type="primary" :loading="loading" @click="handleSubmit">
          {{ mode === 'create' ? '建立' : '儲存' }}
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
}
</style>
