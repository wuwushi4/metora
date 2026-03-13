import type { User } from '@/types/user'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import i18n from '@/i18n'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isLoading = ref(false)

  // 新增: 初始化狀態追蹤
  const isInitialized = ref(false) // 是否完成初始化
  const isInitializing = ref(false) // 是否正在初始化
  const initError = ref<string | null>(null) // 初始化錯誤
  const isLoggingOut = ref(false) // 是否正在登出

  // Getters
  const isAuthenticated = computed(() => !!user.value)
  const isReady = computed(() => isInitialized.value && !isInitializing.value)

  // Actions

  /**
   * 從後端獲取當前使用者資訊
   * 使用 cookie 中的 token 驗證
   */
  async function fetchCurrentUser(): Promise<User | null> {
    try {
      const { getCurrentUser } = await import('@/api/auth')
      const response = await getCurrentUser()
      return response.data ?? null // 確保返回 null 而非 undefined
    }
    catch (error: any) {
      // 401 表示未登入,這是正常情況
      if (error.response?.status === 401) {
        console.log('User not authenticated')
        return null
      }

      // 其他錯誤記錄
      console.error('Failed to fetch current user:', error)
      throw error
    }
  }

  /**
   * 初始化認證狀態
   * 從 cookie 中的 token 獲取使用者資訊
   */
  async function initAuth() {
    // 防止重複初始化
    if (isInitializing.value || isInitialized.value) {
      console.log('Already initialized or initializing')
      return
    }

    isInitializing.value = true
    initError.value = null

    try {
      // 嘗試從 cookie 中的 token 獲取使用者資訊
      const userData = await fetchCurrentUser()

      if (userData) {
        user.value = userData
      }
      else {
        user.value = null
        console.log('No valid authentication found')
      }
    }
    catch (error: any) {
      console.error('Init auth failed:', error)
      initError.value = error.message || i18n.global.t('auth.initFailed')
      user.value = null
    }
    finally {
      isInitialized.value = true
      isInitializing.value = false
    }
  }

  /**
   * 使用者登入
   */
  async function login(username: string, password: string) {
    isLoading.value = true
    try {
      // 呼叫後端登入 API
      const { login: loginApi } = await import('@/api/auth')
      const response = await loginApi(username, password)

      // 直接設定使用者資訊,不儲存到 localStorage
      user.value = response.user

      return response
    }
    catch (error) {
      // 登入失敗時清除任何殘留的認證資訊
      user.value = null
      throw error
    }
    finally {
      isLoading.value = false
    }
  }

  /**
   * 使用者登出
   */
  async function logout() {
    // ⭐ 關鍵: 立即設定登出狀態,阻止後續的 API 請求
    isLoggingOut.value = true
    user.value = null // 立即清除使用者狀態

    // ⭐ 清空所有業務狀態
    try {
      const { useChatStore } = await import('@/stores/chat')
      const { usePromptsStore } = await import('@/stores/prompts')

      const chatStore = useChatStore()
      const promptsStore = usePromptsStore()

      // 清空 Chat Store
      chatStore.resetStore()

      // 清空 Prompts Store
      promptsStore.clearState()
    }
    catch (error) {
      console.error('Failed to clear stores:', error)
    }

    isLoading.value = true
    try {
      // 呼叫後端登出 API
      const { logout: logoutApi } = await import('@/api/auth')
      await logoutApi()
    }
    catch (error) {
      // 即使 API 呼叫失敗,也要清除本地認證狀態
      console.error('Logout API failed:', error)
    }
    finally {
      isLoading.value = false
      // 登出完成後重置標誌 (但保持 user.value = null)
      isLoggingOut.value = false
    }
  }

  /**
   * 刷新 Token
   * 當 access token 過期時自動呼叫此方法獲取新的 token
   */
  async function refreshAccessToken(): Promise<void> {
    try {
      // 呼叫後端刷新 token API
      const { refreshToken: refreshTokenApi } = await import('@/api/auth')
      await refreshTokenApi() // cookie 會自動更新
    }
    catch (error: any) {
      // ⭐ 改進: 只在非 401 錯誤時輸出 (401 表示正常的未登入狀態)
      if (error.response?.status !== 401) {
        console.error('Token refresh failed:', error)
      }

      // 清除認證狀態
      user.value = null

      throw error
    }
  }

  return {
    // State
    user,
    isLoading,
    isInitialized,
    isInitializing,
    initError,
    isLoggingOut,
    // Getters
    isAuthenticated,
    isReady,
    // Actions
    login,
    logout,
    refreshAccessToken,
    initAuth,
    fetchCurrentUser,
  }
})
