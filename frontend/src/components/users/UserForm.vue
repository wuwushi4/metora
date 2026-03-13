<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules } from 'naive-ui'
import type { UserCreateRequest, UserResponse, UserUpdateRequest } from '@/types/user'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSelect,
  NSpace,
  NSwitch,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from '@/utils/message'

interface Props {
  show: boolean
  mode: 'create' | 'edit'
  user?: UserResponse | null
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  mode: 'create',
  user: null,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: UserCreateRequest | UserUpdateRequest]
}>()

const { t } = useI18n()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)

// 表單資料（包含確認密碼欄位用於驗證）
const formData = ref<UserCreateRequest & { confirmPassword?: string }>({
  username: '',
  email: '',
  password: '',
  full_name: '',
  roles: ['user'],
  confirmPassword: '',
})

// 編輯模式的表單資料
const editFormData = ref<UserUpdateRequest>({
  email: '',
  full_name: '',
  is_active: true,
})

// 角色選項
const roleOptions = computed(() => [
  { label: t('users.form.roleOptions.admin'), value: 'admin' },
  { label: t('users.form.roleOptions.user'), value: 'user' },
  { label: t('users.form.roleOptions.editor'), value: 'editor' },
  { label: t('users.form.roleOptions.viewer'), value: 'viewer' },
])

// 表單標題
const title = computed(() => {
  return props.mode === 'create' ? t('users.form.createTitle') : t('users.form.editTitle')
})

// 自訂密碼驗證
function validatePassword(_rule: FormItemRule, value: string): boolean | Error {
  if (props.mode === 'edit')
    return true
  if (!value) {
    return new Error(t('users.form.passwordRequired'))
  }
  if (value.length < 6) {
    return new Error(t('users.form.passwordMinLength'))
  }
  return true
}

// 自訂確認密碼驗證
function validateConfirmPassword(_rule: FormItemRule, value: string): boolean | Error {
  if (props.mode === 'edit')
    return true
  if (!value) {
    return new Error(t('users.form.confirmPasswordRequired'))
  }
  if (value !== formData.value.password) {
    return new Error(t('users.form.confirmPasswordMismatch'))
  }
  return true
}

// 驗證規則 - 新增模式
const createRules = computed<FormRules>(() => ({
  username: [
    { required: true, message: t('users.form.usernameRequired'), trigger: 'blur' },
    { min: 3, max: 50, message: t('users.form.usernameLength'), trigger: 'blur' },
  ],
  email: [
    { required: true, message: t('users.form.emailRequired'), trigger: 'blur' },
    { type: 'email', message: t('users.form.emailInvalid'), trigger: 'blur' },
  ],
  password: [
    { required: true, validator: validatePassword, trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: ['blur', 'password-input'] },
  ],
  roles: [
    { type: 'array', required: true, message: t('users.form.rolesRequired'), trigger: 'change' },
  ],
}))

// 驗證規則 - 編輯模式
const editRules = computed<FormRules>(() => ({
  email: [
    { required: true, message: t('users.form.emailRequired'), trigger: 'blur' },
    { type: 'email', message: t('users.form.emailInvalid'), trigger: 'blur' },
  ],
}))

// 當前驗證規則
const rules = computed(() => {
  return props.mode === 'create' ? createRules.value : editRules.value
})

// 監聽 user prop 變化,更新表單資料
watch(() => props.user, (newUser) => {
  if (newUser && props.mode === 'edit') {
    editFormData.value = {
      email: newUser.email,
      full_name: newUser.full_name || '',
      is_active: newUser.is_active,
    }
  }
}, { immediate: true })

// 監聽 show prop 變化,重置表單
watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
  else if (newShow && props.mode === 'create') {
    // 新增模式時重置為預設值
    formData.value = {
      username: '',
      email: '',
      password: '',
      full_name: '',
      roles: ['user'],
      confirmPassword: '',
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
      // 新增模式 - 移除 confirmPassword 欄位後再提交
      const { confirmPassword, ...createData } = formData.value
      emit('submit', createData as UserCreateRequest)
    }
    else {
      // 編輯模式
      emit('submit', editFormData.value)
    }
  }
  catch (error: any) {
    console.error('表單驗證失敗:', error)
    message.error(t('users.form.validationFailed'))
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
        <NFormItem path="username" :label="$t('users.form.usernameLabel')">
          <NInput
            v-model:value="formData.username"
            :placeholder="$t('users.form.usernamePlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="email" :label="$t('users.form.emailLabel')">
          <NInput
            v-model:value="formData.email"
            :placeholder="$t('users.form.emailPlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="password" :label="$t('users.form.passwordLabel')">
          <NInput
            v-model:value="formData.password"
            type="password"
            :placeholder="$t('users.form.passwordPlaceholder')"
            show-password-on="click"
            clearable
          />
        </NFormItem>

        <NFormItem path="confirmPassword" :label="$t('users.form.confirmPasswordLabel')">
          <NInput
            v-model:value="formData.confirmPassword"
            type="password"
            :placeholder="$t('users.form.confirmPasswordPlaceholder')"
            show-password-on="click"
            clearable
          />
        </NFormItem>

        <NFormItem path="full_name" :label="$t('users.form.fullNameLabel')">
          <NInput
            v-model:value="formData.full_name"
            :placeholder="$t('users.form.fullNamePlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="roles" :label="$t('users.form.rolesLabel')">
          <NSelect
            v-model:value="formData.roles"
            :options="roleOptions"
            multiple
            :placeholder="$t('users.form.rolesPlaceholder')"
          />
        </NFormItem>
      </template>

      <!-- 編輯模式 -->
      <template v-else>
        <NFormItem :label="$t('users.form.usernameLabel')">
          <NInput :value="user?.username" disabled />
        </NFormItem>

        <NFormItem path="email" :label="$t('users.form.emailLabel')">
          <NInput
            v-model:value="editFormData.email"
            :placeholder="$t('users.form.emailPlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="full_name" :label="$t('users.form.fullNameLabel')">
          <NInput
            v-model:value="editFormData.full_name"
            :placeholder="$t('users.form.fullNamePlaceholder')"
            clearable
          />
        </NFormItem>

        <NFormItem path="is_active" :label="$t('users.form.statusLabel')">
          <NSwitch v-model:value="editFormData.is_active">
            <template #checked>
              {{ $t('common.status.enabled') }}
            </template>
            <template #unchecked>
              {{ $t('common.status.disabled') }}
            </template>
          </NSwitch>
        </NFormItem>

        <div class="form-tip">
          <p class="tip-text">
            💡 {{ $t('users.form.tipEdit') }}
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
}
</style>
