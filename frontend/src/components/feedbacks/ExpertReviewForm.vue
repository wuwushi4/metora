<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'
import type { ExpertReviewRequest } from '@/types/feedback'
import { NButton, NCard, NForm, NFormItem, NInput } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { submitExpertReview } from '@/api/feedback'
import { message } from '@/utils/message'

const props = defineProps<{
  feedbackId: string
}>()

const emit = defineEmits<{
  submit: []
}>()

const { t } = useI18n()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const formData = ref<ExpertReviewRequest>({
  expert_opinion: '',
  suggested_response: '',
})

const rules: FormRules = {
  expert_opinion: [
    { required: true, message: t('feedbacks.expertReview.opinionRequired'), trigger: 'blur' },
    { min: 10, message: t('feedbacks.expertReview.opinionMinLength'), trigger: 'blur' },
  ],
}

async function handleSubmit() {
  try {
    // 驗證表單
    await formRef.value?.validate()
  }
  catch {
    message.warning(t('feedbacks.expertReview.validationFailed'))
    return
  }

  loading.value = true
  try {
    await submitExpertReview(props.feedbackId, formData.value)
    message.success(t('feedbacks.expertReview.success'))
    emit('submit')

    // 清空表單
    formData.value = {
      expert_opinion: '',
      suggested_response: '',
    }
  }
  catch (error: any) {
    console.error('提交專家審查失敗:', error)
    message.error(error.message || t('feedbacks.expertReview.failed'))
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <NCard :title="$t('feedbacks.expertReview.title')">
    <NForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="top"
      label-width="auto"
      require-mark-placement="right-hanging"
    >
      <NFormItem :label="$t('feedbacks.expertReview.opinionLabel')" path="expert_opinion">
        <NInput
          v-model:value="formData.expert_opinion"
          type="textarea"
          :rows="5"
          :placeholder="$t('feedbacks.expertReview.opinionPlaceholder')"
          :maxlength="1000"
          show-count
        />
      </NFormItem>

      <NFormItem :label="$t('feedbacks.expertReview.suggestedResponseLabel')" path="suggested_response">
        <NInput
          v-model:value="formData.suggested_response"
          type="textarea"
          :rows="8"
          :placeholder="$t('feedbacks.expertReview.suggestedResponsePlaceholder')"
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
          {{ $t('feedbacks.expertReview.submitReview') }}
        </NButton>
      </NFormItem>
    </NForm>
  </NCard>
</template>
