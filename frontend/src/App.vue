<script setup lang="ts">
import { NConfigProvider, NSpin } from 'naive-ui'
import { computed } from 'vue'
import OfflineIndicator from '@/components/pwa/OfflineIndicator.vue'
import PwaInstallPrompt from '@/components/pwa/PwaInstallPrompt.vue'
import PwaUpdatePrompt from '@/components/pwa/PwaUpdatePrompt.vue'
import { useLocale } from '@/composables/useLocale'
import { usePwa } from '@/composables/usePwa'
import { themeOverrides } from '@/config/naive-theme'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { naiveLocale, naiveDateLocale } = useLocale()
const {
  needRefresh,
  applyUpdate,
  dismissUpdate,
  canInstall,
  isIosSafari,
  installApp,
  dismissInstall,
  isOnline,
} = usePwa()

// 是否顯示初始化 loading
const showInitLoading = computed(() => {
  return !authStore.isInitialized || authStore.isInitializing
})

// 是否顯示錯誤
const showInitError = computed(() => {
  return authStore.isInitialized && !!authStore.initError
})

// 重試初始化
function retryInit() {
  authStore.isInitialized = false
  authStore.initAuth()
}
</script>

<template>
  <NConfigProvider
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
    :theme-overrides="themeOverrides"
  >
    <div id="app">
      <!-- 初始化 Loading -->
      <div v-if="showInitLoading" class="init-loading">
        <div class="loading-content">
          <div class="logo-container">
            <span class="logo-text">M</span>
          </div>
          <h2 class="loading-title">
            Metora
          </h2>
          <NSpin size="medium" stroke="white" />
          <p class="loading-text">
            {{ $t('app.loadingApp') }}
          </p>
        </div>
      </div>

      <!-- 初始化錯誤 -->
      <div v-else-if="showInitError" class="init-error">
        <div class="error-content">
          <div class="error-icon">
            ⚠️
          </div>
          <h2 class="error-title">
            {{ $t('app.initError') }}
          </h2>
          <p class="error-message">
            {{ authStore.initError }}
          </p>
          <button class="retry-button" @click="retryInit">
            {{ $t('app.retry') }}
          </button>
        </div>
      </div>

      <!-- 主應用 -->
      <RouterView v-else v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </div>

    <OfflineIndicator :show="!isOnline" />
    <PwaUpdatePrompt
      :show="needRefresh"
      @update="applyUpdate"
      @dismiss="dismissUpdate"
    />
    <PwaInstallPrompt
      :show="canInstall || isIosSafari"
      :is-ios="isIosSafari"
      @install="installApp"
      @dismiss="dismissInstall"
    />
  </NConfigProvider>
</template>

<style scoped>
#app {
  min-height: 100vh;
}

/* 初始化 Loading 樣式 */
.init-loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
}

.loading-content {
  text-align: center;
  color: white;
}

.logo-container {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

.logo-text {
  font-size: 3rem;
  font-weight: 700;
}

.loading-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 32px;
  letter-spacing: -0.02em;
}

.loading-text {
  margin-top: 16px;
  font-size: 0.875rem;
  opacity: 0.9;
}

/* 初始化錯誤樣式 */
.init-error {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
}

.error-content {
  text-align: center;
  padding: 48px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  max-width: 400px;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
}

.error-message {
  color: #6b7280;
  margin-bottom: 24px;
}

.retry-button {
  padding: 10px 24px;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.retry-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.retry-button:active {
  transform: translateY(0);
}

/* 頁面切換動畫 */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
