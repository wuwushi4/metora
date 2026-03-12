import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'
import { createAuthGuard } from './guards/auth.guard'
import { createLoginGuard } from './guards/login.guard'
import { createRoleGuard } from './guards/role.guard'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagement.vue'),
        meta: {
          requiresAuth: true,
          requiresRoles: ['admin'], // 需要管理員權限
        },
      },
      {
        path: 'collections',
        name: 'CollectionManagement',
        component: () => import('@/views/CollectionManagement.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'collections/:id',
        name: 'CollectionDetail',
        component: () => import('@/views/CollectionDetail.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'regulations',
        name: 'RegulationManagement',
        component: () => import('@/views/RegulationManagement.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'regulations/:id',
        name: 'RegulationDetail',
        component: () => import('@/views/RegulationDetail.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'law-processing',
        name: 'LawProcessing',
        component: () => import('@/views/LawProcessing.vue'),
        meta: {
          requiresAuth: true,
        },
      },
      {
        path: 'feedbacks',
        name: 'FeedbackManagement',
        component: () => import('@/views/FeedbackManagement.vue'),
        meta: {
          requiresAuth: true,
          requiresRoles: ['admin'],
        },
      },
      {
        path: 'feedbacks/:id',
        name: 'FeedbackDetail',
        component: () => import('@/views/FeedbackDetail.vue'),
        meta: {
          requiresAuth: true,
          requiresRoles: ['admin'],
        },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: {
          requiresAuth: true,
          requiresRoles: ['admin'],
        },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 模組化守衛
router.beforeEach(createAuthGuard())
router.beforeEach(createLoginGuard())
router.beforeEach(createRoleGuard())

export default router
