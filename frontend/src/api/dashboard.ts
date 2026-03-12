import type { ApiResponse } from '@/types/api'
import type { AdminDashboardStats, TimeRange, UserDashboardInfo } from '@/types/dashboard'
/**
 * Dashboard API 請求
 */
import request from './request'

/**
 * 取得 Admin 儀表板統計
 */
export function getAdminDashboardStats(timeRange: TimeRange = 'all'): Promise<ApiResponse<AdminDashboardStats>> {
  return request.get('/v1/dashboard/admin/stats', {
    params: { time_range: timeRange },
  })
}

/**
 * 取得 User 儀表板資訊
 */
export function getUserDashboardInfo(): Promise<ApiResponse<UserDashboardInfo>> {
  return request.get('/v1/dashboard/user/info')
}
