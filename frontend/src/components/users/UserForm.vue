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
const roleOptions = [
  { label: '管理員', value: 'admin' },
  { label: '一般使用者', value: 'user' },
  { label: '編輯者', value: 'editor' },
  { label: '檢視者', value: 'viewer' },
]

// 表單標題
const title = computed(() => {
  return props.mode === 'create' ? '新增使用者' : '編輯使用者'
})

// 自訂密碼驗證
function validatePassword(_rule: FormItemRule, value: string): boolean | Error {
  if (props.mode === 'edit')
    return true
  if (!value) {
    return new Error('請輸入密碼')
  }
  if (value.length < 6) {
    return new Error('密碼長度至少 6 個字元')
  }
  return true
}

// 自訂確認密碼驗證
function validateConfirmPassword(_rule: FormItemRule, value: string): boolean | Error {
  if (props.mode === 'edit')
    return true
  if (!value) {
    return new Error('請確認密碼')
  }
  if (value !== formData.value.password) {
    return new Error('兩次輸入的密碼不一致')
  }
  return true
}

// 驗證規則 - 新增模式
const createRules: FormRules = {
  username: [
    { required: true, message: '請輸入使用者名稱', trigger: 'blur' },
    { min: 3, max: 50, message: '長度在 3 到 50 個字元', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '請輸入電子郵件', trigger: 'blur' },
    { type: 'email', message: '請輸入有效的電子郵件', trigger: 'blur' },
  ],
  password: [
    { required: true, validator: validatePassword, trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: ['blur', 'password-input'] },
  ],
  roles: [
    { type: 'array', required: true, message: '請選擇至少一個角色', trigger: 'change' },
  ],
}

// 驗證規則 - 編輯模式
const editRules: FormRules = {
  email: [
    { required: true, message: '請輸入電子郵件', trigger: 'blur' },
    { type: 'email', message: '請輸入有效的電子郵件', trigger: 'blur' },
  ],
}

// 當前驗證規則
const rules = computed(() => {
  return props.mode === 'create' ? createRules : editRules
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
        <NFormItem path="username" label="使用者名稱">
          <NInput
            v-model:value="formData.username"
            placeholder="請輸入使用者名稱"
            clearable
          />
        </NFormItem>

        <NFormItem path="email" label="電子郵件">
          <NInput
            v-model:value="formData.email"
            placeholder="請輸入電子郵件"
            clearable
          />
        </NFormItem>

        <NFormItem path="password" label="密碼">
          <NInput
            v-model:value="formData.password"
            type="password"
            placeholder="請輸入密碼（至少 6 個字元）"
            show-password-on="click"
            clearable
          />
        </NFormItem>

        <NFormItem path="confirmPassword" label="確認密碼">
          <NInput
            v-model:value="formData.confirmPassword"
            type="password"
            placeholder="請再次輸入密碼"
            show-password-on="click"
            clearable
          />
        </NFormItem>

        <NFormItem path="full_name" label="真實姓名">
          <NInput
            v-model:value="formData.full_name"
            placeholder="請輸入真實姓名（可選）"
            clearable
          />
        </NFormItem>

        <NFormItem path="roles" label="角色">
          <NSelect
            v-model:value="formData.roles"
            :options="roleOptions"
            multiple
            placeholder="請選擇角色"
          />
        </NFormItem>
      </template>

      <!-- 編輯模式 -->
      <template v-else>
        <NFormItem label="使用者名稱">
          <NInput :value="user?.username" disabled />
        </NFormItem>

        <NFormItem path="email" label="電子郵件">
          <NInput
            v-model:value="editFormData.email"
            placeholder="請輸入電子郵件"
            clearable
          />
        </NFormItem>

        <NFormItem path="full_name" label="真實姓名">
          <NInput
            v-model:value="editFormData.full_name"
            placeholder="請輸入真實姓名（可選）"
            clearable
          />
        </NFormItem>

        <NFormItem path="is_active" label="狀態">
          <NSwitch v-model:value="editFormData.is_active">
            <template #checked>
              啟用
            </template>
            <template #unchecked>
              停用
            </template>
          </NSwitch>
        </NFormItem>

        <div class="form-tip">
          <p class="tip-text">
            💡 提示：使用者名稱不可修改。如需修改密碼,請使用密碼重置功能。
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
