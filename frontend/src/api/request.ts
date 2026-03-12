import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'
import { handleApiError } from '@/utils/error-handler'

// 創建 axios 實例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  withCredentials: true, // 重要：允許發送 cookies
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 顯示錯誤訊息
 * 使用統一的全域 Message API
 */
async function showErrorMessage(content: string) {
  const { message } = await import('@/utils/message')
  message.error(content, {
    duration: 3000,
    keepAliveOnHover: true,
  })
}

// 請求攔截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Cookie 會自動發送，不需要手動添加 token
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// 用於避免多個請求同時刷新 token
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

function processQueue(error: any = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    }
    else {
      prom.resolve()
    }
  })

  failedQueue = []
}

// 響應攔截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    // 處理 401 錯誤：嘗試自動刷新 token
    if (error.response?.status === 401 && !originalRequest._retry) {
      // ⭐ 檢查是否為認證檢查端點 (/auth/me)
      const isAuthCheckEndpoint = originalRequest.url?.includes('/auth/me')

      // 如果是 refresh、login 或 me 端點失敗，不刷新 token
      if (originalRequest.url?.includes('/auth/refresh')
        || originalRequest.url?.includes('/auth/login')
        || isAuthCheckEndpoint) {
        // 清除認證資訊並導向登入頁
        const { default: router } = await import('@/router')

        // ⭐ 只在非登入頁時才跳轉 (避免重複跳轉)
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }

        return Promise.reject(error)
      }

      // 如果正在刷新，將請求加入隊列
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(() => {
            return request(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // 嘗試刷新 token
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()
        await authStore.refreshAccessToken()

        // 刷新成功，處理隊列中的請求
        processQueue()
        isRefreshing = false

        // 重試原請求
        return request(originalRequest)
      }
      catch (refreshError) {
        // 刷新失敗，清除隊列並登出
        processQueue(refreshError)
        isRefreshing = false

        // 清除記憶體中的使用者資訊
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()
        authStore.user = null

        // ⭐ 清空業務狀態
        try {
          const { useChatStore } = await import('@/stores/chat')
          const { usePromptsStore } = await import('@/stores/prompts')

          const chatStore = useChatStore()
          const promptsStore = usePromptsStore()

          chatStore.resetStore()
          promptsStore.clearState()
        }
        catch (error) {
          console.error('Failed to clear stores on token refresh failure:', error)
        }

        const { default: router } = await import('@/router')
        router.push('/login')

        return Promise.reject(refreshError)
      }
    }

    // 其他錯誤處理
    const errorInfo = handleApiError(error, {
      showMessage: true,
      redirectOnUnauthorized: false, // 已在上面處理
    })

    // 顯示錯誤訊息
    if (errorInfo.showMessage) {
      await showErrorMessage(errorInfo.message)
    }

    return Promise.reject(error)
  },
)

export default request

// 封裝常用方法
export function get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.get(url, config)
}

export function post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request.post(url, data, config)
}

export function put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request.put(url, data, config)
}

export function patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request.patch(url, data, config)
}

export function del<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.delete(url, config)
}
