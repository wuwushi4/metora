<script setup lang="ts">
import type { AssignRolesRequest, UserResponse } from '@/types/user'
import {
  NButton,
  NDivider,
  NModal,
  NSelect,
  NSpace,
  NTag,
  NText,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

interface Props {
  show: boolean
  user: UserResponse | null
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  user: null,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'submit': [data: AssignRolesRequest]
}>()

const { t } = useI18n()

const loading = ref(false)
const selectedRoles = ref<string[]>([])

// 所有可用角色選項
const roleOptions = computed(() => [
  { label: t('users.form.roleOptions.admin'), value: 'admin' },
  { label: t('users.form.roleOptions.user'), value: 'user' },
  { label: t('users.form.roleOptions.editor'), value: 'editor' },
  { label: t('users.form.roleOptions.viewer'), value: 'viewer' },
])

// 角色顏色映射
const roleColors: Record<string, 'error' | 'success' | 'warning' | 'info' | 'default'> = {
  admin: 'error',
  user: 'success',
  editor: 'warning',
  viewer: 'info',
}

// 計算當前角色標籤
const currentRoleTags = computed(() => {
  if (!props.user || !props.user.roles || props.user.roles.length === 0) {
    return [{ label: t('users.roleAssign.noRole'), type: 'default' as const }]
  }
  return props.user.roles.map(role => ({
    label: role,
    type: roleColors[role] || ('default' as const),
  }))
})

// 監聽 user prop 變化,更新選中的角色
watch(() => props.user, (newUser) => {
  if (newUser) {
    selectedRoles.value = [...(newUser.roles || [])]
  }
}, { immediate: true })

// 監聽 show prop 變化
watch(() => props.show, (newShow) => {
  if (newShow && props.user) {
    selectedRoles.value = [...(props.user.roles || [])]
  }
})

// 關閉彈窗
function handleClose() {
  emit('update:show', false)
}

// 提交角色分配
async function handleSubmit() {
  if (selectedRoles.value.length === 0) {
    console.warn('至少需要選擇一個角色')
    return
  }

  loading.value = true
  try {
    emit('submit', { roles: selectedRoles.value })
  }
  finally {
    loading.value = false
  }
}

// 判斷角色是否有變更
const hasChanges = computed(() => {
  const currentRoles = props.user?.roles || []
  if (currentRoles.length !== selectedRoles.value.length)
    return true
  return !currentRoles.every(role => selectedRoles.value.includes(role))
})
</script>

<template>
  <NModal
    :show="show"
    :mask-closable="false"
    preset="card"
    :title="$t('users.roleAssign.title')"
    style="width: 520px"
    @update:show="handleClose"
  >
    <div v-if="user" class="role-assign-content">
      <!-- 使用者資訊 -->
      <div class="user-info">
        <div class="info-row">
          <span class="label">{{ $t('users.roleAssign.usernameLabel') }}</span>
          <span class="value">{{ user.username }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('users.roleAssign.emailLabel') }}</span>
          <span class="value">{{ user.email }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('users.roleAssign.statusLabel') }}</span>
          <NTag :type="user.is_active ? 'success' : 'default'" size="small">
            {{ user.is_active ? $t('common.status.enabled') : $t('common.status.disabled') }}
          </NTag>
        </div>
      </div>

      <NDivider />

      <!-- 當前角色 -->
      <div class="current-roles">
        <NText strong class="section-title">
          {{ $t('users.roleAssign.currentRoles') }}
        </NText>
        <NSpace :size="8" class="role-tags">
          <NTag
            v-for="tag in currentRoleTags"
            :key="tag.label"
            :type="tag.type"
            size="medium"
          >
            {{ tag.label }}
          </NTag>
        </NSpace>
      </div>

      <NDivider />

      <!-- 角色選擇 -->
      <div class="role-selector">
        <NText strong class="section-title">
          {{ $t('users.roleAssign.assignRoles') }}
        </NText>
        <NSelect
          v-model:value="selectedRoles"
          :options="roleOptions"
          multiple
          :placeholder="$t('users.roleAssign.selectRolePlaceholder')"
          clearable
          size="medium"
        />
        <div class="role-tips">
          <p class="tip-item">
            💡 {{ $t('users.roleAssign.tipMinRole') }}
          </p>
          <p class="tip-item">
            🔒 {{ $t('users.roleAssign.tipSuperAdmin') }}
          </p>
        </div>
      </div>
    </div>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">
          {{ $t('common.actions.cancel') }}
        </NButton>
        <NButton
          type="primary"
          :loading="loading"
          :disabled="!hasChanges || selectedRoles.length === 0"
          @click="handleSubmit"
        >
          {{ $t('common.actions.save') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.role-assign-content {
  padding: 4px 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}

.label {
  font-weight: 500;
  color: #6b7280;
  min-width: 100px;
}

.value {
  color: #111827;
}

.section-title {
  display: block;
  margin-bottom: 12px;
  font-size: 0.9375rem;
  color: #111827;
}

.current-roles {
  margin: 8px 0;
}

.role-tags {
  margin-top: 12px;
}

.role-selector {
  margin: 8px 0;
}

.role-tips {
  margin-top: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.tip-item {
  margin: 0;
  margin-bottom: 8px;
  font-size: 0.8125rem;
  color: #6b7280;
  line-height: 1.5;
}

.tip-item:last-child {
  margin-bottom: 0;
}
</style>
