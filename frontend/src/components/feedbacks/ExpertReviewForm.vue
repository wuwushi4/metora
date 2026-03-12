<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import type { ExpertReviewRequest } from '@/types/feedback'
import { NButton, NCard, NForm, NFormItem, NInput } from 'naive-ui'
import { ref } from 'vue'
import { submitExpertReview } from '@/api/feedback'
import { message } from '@/utils/message'

const props = defineProps<{
  feedbackId: string
}>()

const emit = defineEmits<{
  submit: []
}>()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const formData = ref<ExpertReviewRequest>({
  expert_opinion: '',
  suggested_response: '',
})

const rules: FormRules = {
  expert_opinion: [
    { required: true, message: '請輸入專家意見', trigger: 'blur' },
    { min: 10, message: '專家意見至少需要 10 個字元', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  try {
    // 驗證表單
    await formRef.value?.validate()
  }
  catch {
    message.warning('請檢查表單填寫是否正確')
    return
  }

  loading.value = true
  try {
    await submitExpertReview(props.feedbackId, formData.value)
    message.success('專家審查提交成功')
    emit('submit')

    // 清空表單
    formData.value = {
      expert_opinion: '',
      suggested_response: '',
    }
  }
  catch (error: any) {
    console.error('提交專家審查失敗:', error)
    message.error(error.message || '提交專家審查失敗')
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <NCard title="專家審查">
    <NForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="top"
      label-width="auto"
      require-mark-placement="right-hanging"
    >
      <NFormItem label="專家意見" path="expert_opinion">
        <NInput
          v-model:value="formData.expert_opinion"
          type="textarea"
          :rows="5"
          placeholder="請輸入您的專業意見,包括問題分析、原因判斷等 (至少 10 個字元)"
          :maxlength="1000"
          show-count
        />
      </NFormItem>

      <NFormItem label="建議回覆內容 (選填)" path="suggested_response">
        <NInput
          v-model:value="formData.suggested_response"
          type="textarea"
          :rows="8"
          placeholder="如果認為 AI 回覆不當,請提供建議的回覆內容(用於 DPO 微調)"
          :maxlength="2000"
          show-count
        />
      </NFormItem>

      <NFormItem>
        <NButton
          type="primary"
          :loading="loading"
          :disabled="loading"
          @click="handleSubmit"
        >
          提交審查
        </NButton>
      </NFormItem>
    </NForm>
  </NCard>
</template>
