import type { ApiResponse } from '@/types/api'
import type { ChangePasswordRequest, LoginResponse, User } from '@/types/user'
import { get, post } from './request'

/**
 * 登入 API
 *
 * @param username - 使用者名稱或電子郵件
 * @param password - 密碼
 * @returns 登入響應（包含 tokens 和使用者資訊）
 */
export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await post<ApiResponse<LoginResponse>>('/v1/auth/login', {
    username,
    password,
  })

  // 後端統一響應格式，資料在 data 欄位中
  if (!response.data) {
    throw new Error('登入失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 登出 API
 */
export async function logout(): Promise<void> {
  await post<ApiResponse<{ message: string }>>('/v1/auth/logout')
}

/**
 * 刷新訪問令牌 API
 */
export async function refreshToken(): Promise<void> {
  await post<ApiResponse<{ message: string }>>('/v1/auth/refresh')
}

/**
 * 驗證 token API
 */
export async function verifyToken(): Promise<void> {
  await get<ApiResponse<{ message: string }>>('/v1/auth/verify')
}

/**
 * 修改密碼 API
 *
 * @param data - 修改密碼請求資料（舊密碼和新密碼）
 */
export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await post<ApiResponse<{ message: string }>>('/v1/auth/change-password', data)
}

/**
 * 獲取當前使用者資訊 API
 * 使用 cookie 中的 token 驗證
 */
export async function getCurrentUser(): Promise<ApiResponse<User>> {
  return await get<ApiResponse<User>>('/v1/auth/me')
}
