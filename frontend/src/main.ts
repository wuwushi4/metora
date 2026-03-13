import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { useAuthStore } from '@/stores/auth'
import i18n from '@/i18n'
import App from './App.vue'
import router from './router'
import './style.css'

/**
 * 非同步初始化應用
 * 等待認證狀態初始化完成後再掛載
 */
async function initializeApp() {
  const app = createApp(App)

  // 初始化 Pinia
  const pinia = createPinia()
  app.use(pinia)

  // 初始化 i18n
  app.use(i18n)

  // 【重要】等待認證狀態初始化完成
  const authStore = useAuthStore()
  await authStore.initAuth()

  // 掛載 router 和 app
  app.use(router)
  app.mount('#app')

  console.log('App initialized successfully')
}

// 取得 fallback 文字（i18n 尚未初始化時使用）
function getFallbackText(key: string): string {
  const locale = localStorage.getItem('locale') || navigator.language
  const isEn = locale.startsWith('en')
  const map: Record<string, [string, string]> = {
    initFailed: ['應用初始化失敗', 'Application initialization failed'],
    unknownError: ['未知錯誤', 'Unknown error'],
    reload: ['重新載入', 'Reload'],
  }
  const entry = map[key]
  return entry ? (isEn ? entry[1] : entry[0]) : key
}

// 啟動應用
initializeApp().catch((error) => {
  console.error('Failed to initialize app:', error)
  // 顯示全域錯誤頁面
  document.body.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);">
      <div style="text-align: center; padding: 48px; background: white; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); max-width: 400px;">
        <div style="font-size: 4rem; margin-bottom: 16px;">⚠️</div>
        <h1 style="font-size: 1.5rem; font-weight: 700; color: #111827; margin-bottom: 12px;">${getFallbackText('initFailed')}</h1>
        <p style="color: #6b7280; margin-bottom: 24px;">${error.message || getFallbackText('unknownError')}</p>
        <button onclick="location.reload()" style="padding: 10px 24px; background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">${getFallbackText('reload')}</button>
      </div>
    </div>
  `
})
