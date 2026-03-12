import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function usePermission() {
  const authStore = useAuthStore()

  const hasRole = (role: string | string[]): boolean => {
    if (!authStore.user)
      return false
    if (authStore.user.is_superuser)
      return true

    const roles = Array.isArray(role) ? role : [role]
    const userRoles = authStore.user.roles || []

    return roles.some(r => userRoles.includes(r))
  }

  const canAccess = computed(() => ({
    users: hasRole('admin'),
    settings: hasRole(['admin', 'editor']),
  }))

  return { hasRole, canAccess }
}
