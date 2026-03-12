import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** 是否需要認證 */
    requiresAuth?: boolean
    /** 需要的角色列表 */
    requiresRoles?: string[]
  }
}
