import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function createAuthGuard() {
  return async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext,
  ) => {
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

    // 等待初始化完成
    if (!authStore.isInitialized) {
      console.log('Waiting for auth initialization...')

      // 輪詢等待初始化完成 (最多等待 10 秒)
      let waitCount = 0
      while (authStore.isInitializing && waitCount < 200) {
        await new Promise(resolve => setTimeout(resolve, 50))
        waitCount++
      }

      // 如果超時,記錄錯誤
      if (waitCount >= 200) {
        console.error('Auth initialization timeout')
      }
    }

    // 不需要認證的路由直接放行
    if (!requiresAuth) {
      next()
      return
    }

    // 需要認證但未登入,跳轉登入頁
    if (!authStore.isAuthenticated) {
      next({
        name: 'Login',
        query: { redirect: to.fullPath },
      })
      return
    }

    // 已認證,放行
    next()
  }
}
