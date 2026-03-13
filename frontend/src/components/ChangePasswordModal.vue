<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules } from 'naive-ui'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSpace,
} from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { changePassword } from '@/api/auth'
import { message } from '@/utils/message'

const { t } = useI18n()

interface Props {
  show: boolean
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

// 表單資料
const formData = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

// 自訂新密碼驗證
function validateNewPassword(_rule: FormItemRule, value: string): boolean | Error {
  if (!value) {
    return new Error(t('auth.changePassword.newPasswordRequired'))
  }
  if (value.length < 6) {
    return new Error(t('auth.changePassword.minLength'))
  }
  if (value === formData.value.old_password) {
    return new Error(t('auth.changePassword.notSameAsOld'))
  }
  return true
}

// 自訂確認密碼驗證
function validateConfirmPassword(_rule: FormItemRule, value: string): boolean | Error {
  if (!value) {
    return new Error(t('auth.changePassword.confirmRequired'))
  }
  if (value !== formData.value.new_password) {
    return new Error(t('auth.changePassword.mismatch'))
  }
  return true
}

// 驗證規則
const rules: FormRules = {
  old_password: [
    { required: true, message: () => t('auth.changePassword.currentPasswordRequired'), trigger: 'blur' },
    { min: 6, message: () => t('auth.changePassword.minLength'), trigger: 'blur' },
  ],
  new_password: [
    { required: true, validator: validateNewPassword, trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, validator: validateConfirmPassword, trigger: ['blur', 'password-input'] },
  ],
}

// 監聽 show prop 變化,重置表單
watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})

// 重置表單
function resetForm() {
  formRef.value?.restoreValidation()
  formData.value = {
    old_password: '',
    new_password: '',
    confirm_password: '',
  }
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

    await changePassword({
      old_password: formData.value.old_password,
      new_password: formData.value.new_password,
    })

    message.success(t('auth.changePassword.success'))
    handleClose()
  }
  catch (error: any) {
    console.error('修改密碼失敗:', error)
    message.error(error.message || t('auth.changePassword.failed'))
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
    :title="t('auth.changePassword.title')"
    style="width: 500px"
    @update:show="handleClose"
  >
    <NForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-placement="left"
      label-width="100px"
      require-mark-placement="right-hanging"
    >
      <NFormItem path="old_password" :label="t('auth.changePassword.currentPassword')">
        <NInput
          v-model:value="formData.old_password"
          type="password"
          :placeholder="t('auth.changePassword.currentPasswordPlaceholder')"
          show-password-on="click"
          clearable
        />
      </NFormItem>

      <NFormItem path="new_password" :label="t('auth.changePassword.newPassword')">
        <NInput
          v-model:value="formData.new_password"
          type="password"
          :placeholder="t('auth.changePassword.newPasswordPlaceholder')"
          show-password-on="click"
          clearable
        />
      </NFormItem>

      <NFormItem path="confirm_password" :label="t('auth.changePassword.confirmPassword')">
        <NInput
          v-model:value="formData.confirm_password"
          type="password"
          :placeholder="t('auth.changePassword.confirmPasswordPlaceholder')"
          show-password-on="click"
          clearable
        />
      </NFormItem>

      <div class="form-tip">
        <p class="tip-text">
          {{ t('auth.changePassword.tip') }}
        </p>
      </div>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">
          {{ t('common.actions.cancel') }}
        </NButton>
        <NButton type="primary" :loading="loading" @click="handleSubmit">
          {{ t('auth.changePassword.confirmButton') }}
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
