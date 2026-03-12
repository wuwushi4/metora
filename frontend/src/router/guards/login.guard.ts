import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function createLoginGuard() {
  return (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext,
  ) => {
    const authStore = useAuthStore()

    if (to.name !== 'Login') {
      next()
      return
    }

    if (authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }

    next()
  }
}
