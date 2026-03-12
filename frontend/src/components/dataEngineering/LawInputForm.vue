<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import type { LawProcessRequest } from '@/types/dataEngineering'
import { NButton, NCheckbox, NForm, NFormItem, NInput, NSpace } from 'naive-ui'
import { ref } from 'vue'

interface Props {
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  submit: [data: LawProcessRequest]
}>()

const formRef = ref<FormInst | null>(null)

// 表單資料
const formData = ref<LawProcessRequest>({
  pcode: '',
  law_name: undefined,
  force_refresh: false,
})

// 驗證規則
const rules: FormRules = {
  pcode: [
    { required: true, message: '請輸入法規編號', trigger: 'blur' },
    {
      pattern: /^[A-Z]\d{7}$/,
      message: '格式錯誤，正確格式為：1個大寫英文字母 + 7個數字（例如：M0060027）',
      trigger: 'blur',
    },
  ],
  law_name: [
    { max: 200, message: '法規名稱長度不可超過 200 個字元', trigger: 'blur' },
  ],
}

// 提交表單
async function handleSubmit() {
  try {
    await formRef.value?.validate()
    // 自動轉換 pcode 為大寫
    const requestData = {
      ...formData.value,
      pcode: formData.value.pcode.toUpperCase(),
      law_name: formData.value.law_name?.trim() || undefined,
    }
    emit('submit', requestData)
  }
  catch {
    // 驗證失敗，不做任何處理
  }
}

// 重置表單
function reset() {
  formData.value = {
    pcode: '',
    law_name: undefined,
    force_refresh: false,
  }
}

// 暴露方法給父組件
defineExpose({
  reset,
})
</script>

<template>
  <NForm
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-placement="left"
    label-width="auto"
    require-mark-placement="right-hanging"
  >
    <NFormItem label="法規編號" path="pcode">
      <NInput
        v-model:value="formData.pcode"
        placeholder="例如：M0060027"
        :disabled="loading"
        @keyup.enter="handleSubmit"
      />
    </NFormItem>

    <NFormItem label="法規名稱" path="law_name">
      <NInput
        v-model:value="formData.law_name"
        placeholder="可選，如未提供則從網頁提取"
        :disabled="loading"
        @keyup.enter="handleSubmit"
      />
    </NFormItem>

    <NFormItem label="強制重新爬取">
      <NCheckbox v-model:checked="formData.force_refresh" :disabled="loading">
        忽略快取，重新從網站爬取資料
      </NCheckbox>
    </NFormItem>

    <NFormItem>
      <NSpace>
        <NButton
          type="primary"
          :loading="loading"
          :disabled="loading"
          @click="handleSubmit"
        >
          開始處理
        </NButton>
        <NButton :disabled="loading" @click="reset">
          重置
        </NButton>
      </NSpace>
    </NFormItem>
  </NForm>
</template>
