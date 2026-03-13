<script setup lang="ts">
import { LockClosedOutline, PersonOutline } from '@vicons/ionicons5'
import { NButton, NCard, NForm, NFormItem, NIcon, NInput } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { message } from '@/utils/message'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t } = useI18n()

// 表單資料
const formRef = ref()
const formData = ref({
  username: '',
  password: '',
})

// 輸入框 focus 狀態
const usernameFocused = ref(false)
const passwordFocused = ref(false)

// 表單驗證規則
const rules = {
  username: {
    required: true,
    message: () => t('auth.login.usernameRequired'),
    trigger: 'blur',
  },
  password: {
    required: true,
    message: () => t('auth.login.passwordRequired'),
    trigger: 'blur',
  },
}

// 處理登入
async function handleLogin() {
  try {
    await formRef.value?.validate()

    await authStore.login(formData.value.username, formData.value.password)

    message.success(t('auth.login.success'))

    // 重導向到原來要去的頁面,或預設到首頁
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  }
  catch (error: any) {
    message.error(error.message || t('auth.login.failed'))
  }
}

// Enter 鍵登入
function handleKeyup(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    handleLogin()
  }
}
</script>

<template>
  <div class="login-container">
    <!-- 背景層 -->
    <div class="background-layer">
      <!-- 漸層背景 -->
      <div class="gradient-bg" />

      <!-- 動態網格 -->
      <div class="grid-pattern" />

      <!-- 光暈效果 -->
      <div class="glow glow-1" />
      <div class="glow glow-2" />
      <div class="glow glow-3" />

      <!-- 裝飾性幾何元素 -->
      <div class="geometric-shape shape-1" />
      <div class="geometric-shape shape-2" />
    </div>

    <!-- 登入卡片容器 -->
    <div class="login-card-wrapper">
      <NCard
        :bordered="false"
        class="login-card"
        size="large"
      >
        <!-- Logo 和標題區域 -->
        <div class="brand-section">
          <div class="logo-container">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </div>
          </div>
          <h1 class="brand-title">
            Metora
          </h1>
          <p class="brand-subtitle">
            {{ t('auth.login.subtitle') }}
          </p>
          <div class="title-divider" />
        </div>

        <!-- 表單區域 -->
        <NForm
          ref="formRef"
          :model="formData"
          :rules="rules"
          size="large"
          :show-label="false"
          @keyup="handleKeyup"
        >
          <!-- 帳號輸入 -->
          <NFormItem path="username">
            <div
              class="input-wrapper"
              :class="{ 'input-focused': usernameFocused }"
            >
              <div class="input-icon">
                <NIcon :component="PersonOutline" :size="20" />
              </div>
              <NInput
                v-model:value="formData.username"
                :placeholder="t('auth.login.usernamePlaceholder')"
                class="custom-input"
                @focus="usernameFocused = true"
                @blur="usernameFocused = false"
              >
                <template #suffix>
                  <!-- 佔位空間,確保與密碼框寬度一致 -->
                  <div style="width: 16px;" />
                </template>
              </NInput>
            </div>
          </NFormItem>

          <!-- 密碼輸入 -->
          <NFormItem path="password">
            <div
              class="input-wrapper"
              :class="{ 'input-focused': passwordFocused }"
            >
              <div class="input-icon">
                <NIcon :component="LockClosedOutline" :size="20" />
              </div>
              <NInput
                v-model:value="formData.password"
                type="password"
                :placeholder="t('auth.login.passwordPlaceholder')"
                class="custom-input"
                show-password-on="click"
                @focus="passwordFocused = true"
                @blur="passwordFocused = false"
              />
            </div>
          </NFormItem>

          <!-- 登入按鈕 -->
          <div class="button-container">
            <NButton
              type="primary"
              size="large"
              block
              class="login-button"
              :loading="authStore.isLoading"
              @click="handleLogin"
            >
              <span v-if="!authStore.isLoading">{{ t('auth.login.loginButton') }}</span>
              <span v-else>{{ t('auth.login.loggingIn') }}</span>
            </NButton>
          </div>
        </NForm>
      </NCard>

      <!-- 版權資訊 -->
      <div class="copyright">
        <p>&copy; 2026 Metora. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== 容器佈局 ===== */
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 1rem;
}

/* ===== 背景層 ===== */
.background-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* 深色漸層背景 */
.gradient-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #0c4a6e 50%, #1e293b 75%, #0f172a 100%);
}

/* 網格圖案 */
.grid-pattern {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(50px, 50px);
  }
}

/* 發光效果 */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
  animation: floatGlow 15s ease-in-out infinite;
}

.glow-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #0ea5e9, transparent);
  top: -10%;
  right: -10%;
  animation-delay: 0s;
}

.glow-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #6366f1, transparent);
  bottom: -10%;
  left: -10%;
  animation-delay: 5s;
}

.glow-3 {
  width: 450px;
  height: 450px;
  background: radial-gradient(circle, #3b82f6, transparent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 10s;
}

@keyframes floatGlow {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.15;
  }
  50% {
    transform: translate(30px, -30px) scale(1.1);
    opacity: 0.25;
  }
}

/* 幾何裝飾 */
.geometric-shape {
  position: absolute;
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 12px;
  animation: rotateShape 20s linear infinite;
}

.shape-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: 10%;
  animation-duration: 25s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  bottom: 15%;
  right: 15%;
  animation-duration: 30s;
  animation-direction: reverse;
}

@keyframes rotateShape {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* ===== 登入卡片 ===== */
.login-card-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
}

.login-card {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  box-shadow:
    0 8px 32px 0 rgba(0, 0, 0, 0.37),
    inset 0 1px 0 0 rgba(255, 255, 255, 0.05) !important;
  border-radius: 24px !important;
  padding: 3rem 2.5rem !important;
  transition: all 0.3s ease;
}

.login-card:hover {
  border-color: rgba(255, 255, 255, 0.15) !important;
  box-shadow:
    0 12px 48px 0 rgba(0, 0, 0, 0.5),
    inset 0 1px 0 0 rgba(255, 255, 255, 0.1) !important;
}

/* ===== 品牌區域 ===== */
.brand-section {
  text-align: center;
  margin-bottom: 2.5rem;
}

.logo-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.logo-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  border-radius: 16px;
  color: white;
  box-shadow:
    0 8px 24px rgba(14, 165, 233, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  animation: logoFloat 3s ease-in-out infinite;
}

.logo-icon svg {
  width: 36px;
  height: 36px;
}

@keyframes logoFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.brand-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6, #6366f1);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
  animation: gradientShift 5s ease infinite;
}

@keyframes gradientShift {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.brand-subtitle {
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.875rem;
  letter-spacing: 0.05em;
  margin-bottom: 1.5rem;
}

.title-divider {
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, transparent, #0ea5e9, transparent);
  margin: 0 auto;
  border-radius: 2px;
}

/* ===== 輸入框樣式 ===== */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0 1rem;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
  width: 100%;
  height: 50px;
}

.input-wrapper:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
}

.input-wrapper.input-focused {
  background: rgba(255, 255, 255, 0.07);
  border-color: #0ea5e9;
  box-shadow:
    0 0 0 3px rgba(14, 165, 233, 0.1),
    0 4px 12px rgba(14, 165, 233, 0.2);
}

.input-icon {
  display: flex;
  align-items: center;
  color: rgba(226, 232, 240, 0.5);
  margin-right: 0.75rem;
  transition: color 0.3s ease;
}

.input-focused .input-icon {
  color: #0ea5e9;
}

.custom-input {
  flex: 1;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #e2e8f0 !important;
}

.custom-input::placeholder {
  color: rgba(226, 232, 240, 0.4);
}

/* 移除 Naive UI 輸入框的預設樣式 */
:deep(.n-input__border),
:deep(.n-input__state-border) {
  border: none !important;
  box-shadow: none !important;
}

:deep(.n-input) {
  background: transparent !important;
}

:deep(.n-input__input-el) {
  color: #e2e8f0 !important;
}

:deep(.n-input__placeholder) {
  color: rgba(226, 232, 240, 0.4) !important;
}

/* 確保密碼輸入框的顯示密碼按鈕樣式一致 */
:deep(.n-input__suffix) {
  color: rgba(226, 232, 240, 0.5);
  transition: color 0.3s ease;
}

:deep(.n-input__suffix:hover) {
  color: #0ea5e9;
}

/* 確保兩個輸入框高度一致 */
:deep(.n-input__input) {
  min-height: 50px;
}

:deep(.n-input-wrapper) {
  padding: 0 !important;
}

/* ===== 按鈕樣式 ===== */
.button-container {
  margin-top: 2rem;
}

.login-button {
  height: 50px !important;
  border-radius: 12px !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
  background: linear-gradient(135deg, #0ea5e9, #3b82f6) !important;
  border: none !important;
  box-shadow:
    0 4px 16px rgba(14, 165, 233, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  transition: all 0.3s ease !important;
  position: relative;
  overflow: hidden;
}

.login-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.login-button:hover::before {
  left: 100%;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 24px rgba(14, 165, 233, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
}

.login-button:active {
  transform: translateY(0);
}

/* ===== 版權資訊 ===== */
.copyright {
  margin-top: 2rem;
  text-align: center;
}

.copyright p {
  color: rgba(226, 232, 240, 0.5);
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

/* ===== 響應式設計 ===== */
@media (max-width: 640px) {
  .login-card {
    padding: 2rem 1.5rem !important;
    border-radius: 20px !important;
  }

  .brand-title {
    font-size: 1.75rem;
  }

  .logo-icon {
    width: 56px;
    height: 56px;
  }

  .logo-icon svg {
    width: 32px;
    height: 32px;
  }

  .glow {
    filter: blur(60px);
  }
}

@media (min-width: 768px) {
  .login-card-wrapper {
    max-width: 440px;
  }
}

/* ===== 載入動畫 ===== */
:deep(.n-button__icon) {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
