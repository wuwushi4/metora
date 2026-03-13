<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import type { LawProcessRequest } from '@/types/dataEngineering'
import { NButton, NCheckbox, NForm, NFormItem, NInput, NSpace } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

interface Props {
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  submit: [data: LawProcessRequest]
}>()

const { t } = useI18n()

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
    { required: true, message: t('dataEngineering.form.pcodeRequired'), trigger: 'blur' },
    {
      pattern: /^[A-Z]\d{7}$/,
      message: t('dataEngineering.form.pcodeFormat'),
      trigger: 'blur',
    },
  ],
  law_name: [
    { max: 200, message: t('dataEngineering.form.lawNameMaxLength'), trigger: 'blur' },
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
    <NFormItem :label="$t('dataEngineering.form.pcodeLabel')" path="pcode">
      <NInput
        v-model:value="formData.pcode"
        :placeholder="$t('dataEngineering.form.pcodePlaceholder')"
        :disabled="loading"
        @keyup.enter="handleSubmit"
      />
    </NFormItem>

    <NFormItem :label="$t('dataEngineering.form.lawNameLabel')" path="law_name">
      <NInput
        v-model:value="formData.law_name"
        :placeholder="$t('dataEngineering.form.lawNamePlaceholder')"
        :disabled="loading"
        @keyup.enter="handleSubmit"
      />
    </NFormItem>

    <NFormItem :label="$t('dataEngineering.form.forceRefresh')">
      <NCheckbox v-model:checked="formData.force_refresh" :disabled="loading">
        {{ $t('dataEngineering.form.forceRefreshHint') }}
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
          {{ $t('dataEngineering.form.startProcess') }}
        </NButton>
        <NButton :disabled="loading" @click="reset">
          {{ $t('common.actions.reset') }}
        </NButton>
      </NSpace>
    </NFormItem>
  </NForm>
</template>
