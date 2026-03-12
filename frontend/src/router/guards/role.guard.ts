import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function createRoleGuard() {
  return (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext,
  ) => {
    const authStore = useAuthStore()
    const requiresRoles = to.meta.requiresRoles as string[] | undefined

    if (!requiresRoles || requiresRoles.length === 0) {
      next()
      return
    }

    if (authStore.user?.is_superuser) {
      next()
      return
    }

    const userRoles = authStore.user?.roles || []
    const hasRole = requiresRoles.some(role => userRoles.includes(role))

    if (!hasRole) {
      console.warn(`使用者沒有訪問 ${to.path} 所需的角色: ${requiresRoles.join(', ')}`)
      next({ name: 'Dashboard' })
      return
    }

    next()
  }
}
