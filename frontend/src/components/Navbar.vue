<script setup lang="ts">
import {
  GlobeOutline as GlobeIcon,
  KeyOutline as KeyIcon,
  LogOutOutline as LogoutIcon,
  MenuOutline as MenuIcon,
  NotificationsOutline as NotificationIcon,
  SettingsOutline as SettingsIcon,
  PersonCircleOutline as UserIcon,
} from '@vicons/ionicons5'
import {
  NAvatar,
  NBadge,
  NButton,
  NDropdown,
  NIcon,
  NLayoutHeader,
  NSpace,
} from 'naive-ui'
import { computed, h, markRaw, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import ChangePasswordModal from '@/components/ChangePasswordModal.vue'
import { useLocale } from '@/composables/useLocale'
import { useAuthStore } from '@/stores/auth'
import { message, notification } from '@/utils/message'

const props = defineProps<{
  collapsed: boolean
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
}>()

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()
const { setLocale } = useLocale()

const isLoggingOut = ref(false)
const unreadNotifications = ref(0) // 模擬未讀通知數
const showChangePasswordModal = ref(false)

// 使用 markRaw 防止圖示元件被 reactive 化
const icons = {
  user: markRaw(UserIcon),
  settings: markRaw(SettingsIcon),
  key: markRaw(KeyIcon),
  logout: markRaw(LogoutIcon),
  globe: markRaw(GlobeIcon),
}

// 語言選項
const languageOptions = computed(() => [
  { label: '繁體中文', key: 'zh-TW' },
  { label: 'English', key: 'en' },
])

function handleLanguageSelect(key: string) {
  setLocale(key)
}

// 使用者選單選項
const userOptions = computed(() => [
  {
    label: t('navbar.profile'),
    key: 'profile',
    icon: () => h(NIcon, null, { default: () => h(icons.user) }),
  },
  {
    label: t('navbar.changePassword'),
    key: 'change-password',
    icon: () => h(NIcon, null, { default: () => h(icons.key) }),
  },
  {
    label: t('navbar.settings'),
    key: 'settings',
    icon: () => h(NIcon, null, { default: () => h(icons.settings) }),
  },
  {
    type: 'divider',
    key: 'd1',
  },
  {
    label: t('navbar.logout'),
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(icons.logout) }),
  },
])

// 處理選單選擇
async function handleSelect(key: string) {
  if (key === 'logout') {
    await handleLogout()
  }
  else if (key === 'profile') {
    message.info(t('navbar.profileWip'))
  }
  else if (key === 'change-password') {
    showChangePasswordModal.value = true
  }
  else if (key === 'settings') {
    message.info(t('navbar.settingsWip'))
  }
}

// 處理登出
async function handleLogout() {
  try {
    isLoggingOut.value = true
    await authStore.logout()
    message.success(t('auth.logout.success'))
    router.push('/login')
  }
  catch (error: any) {
    message.error(error.message || t('auth.logout.failed'))
  }
  finally {
    isLoggingOut.value = false
  }
}

// 切換側邊欄
function toggleCollapsed() {
  emit('update:collapsed', !props.collapsed)
}

// 處理通知點擊
function handleNotifications() {
  notification.info({
    title: t('navbar.notifications.title'),
    content: t('navbar.notifications.empty'),
    duration: 3000,
  })
  // TODO: 實作通知中心
}
</script>

<template>
  <NLayoutHeader
    bordered
    class="navbar-header"
  >
    <!-- 左側：選單按鈕與 Logo -->
    <div class="flex items-center gap-4">
      <NButton
        quaternary
        circle
        @click="toggleCollapsed"
      >
        <template #icon>
          <NIcon size="20">
            <MenuIcon />
          </NIcon>
        </template>
      </NButton>

      <div class="flex items-center gap-3">
        <div class="logo-container">
          <span class="logo-text">M</span>
        </div>
        <h1 class="logo-title">
          Metora
        </h1>
      </div>
    </div>

    <!-- 右側：語言切換 & 通知 & 使用者資訊 -->
    <NSpace align="center" :size="16">
      <!-- 語言切換 -->
      <NDropdown
        trigger="click"
        :options="languageOptions"
        @select="handleLanguageSelect"
      >
        <NButton quaternary circle>
          <template #icon>
            <NIcon size="20">
              <GlobeIcon />
            </NIcon>
          </template>
        </NButton>
      </NDropdown>

      <!-- 通知鈴鐺 -->
      <NBadge :value="unreadNotifications" :max="99">
        <NButton
          quaternary
          circle
          @click="handleNotifications"
        >
          <template #icon>
            <NIcon size="20">
              <NotificationIcon />
            </NIcon>
          </template>
        </NButton>
      </NBadge>

      <!-- 使用者選單 -->
      <NDropdown
        trigger="click"
        :options="userOptions"
        @select="handleSelect"
      >
        <div class="user-info">
          <NAvatar
            round
            size="small"
            :src="authStore.user?.avatar_url"
            :fallback-src="`https://api.dicebear.com/7.x/avataaars/svg?seed=${authStore.user?.username}`"
          />
          <div class="user-details">
            <div class="user-name">
              {{ authStore.user?.full_name || authStore.user?.username }}
            </div>
            <div class="user-email">
              {{ authStore.user?.email }}
            </div>
          </div>
        </div>
      </NDropdown>
    </NSpace>

    <!-- 修改密碼彈窗 -->
    <ChangePasswordModal v-model:show="showChangePasswordModal" />
  </NLayoutHeader>
</template>

<style scoped>
.navbar-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  transition:
    background 0.3s ease,
    border-color 0.3s ease;
}

.logo-container {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.3);
}

.logo-text {
  color: white;
  font-weight: 700;
  font-size: 1.125rem;
  letter-spacing: -0.02em;
}

.logo-title {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-info:hover {
  background-color: #f3f4f6;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

@media (max-width: 640px) {
  .user-details {
    display: none;
  }
}

.user-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.2;
}

.user-email {
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.2;
}
</style>
