import type { ApiResponse, PaginationResponse } from '@/types/api'
import type {
  AssignRolesRequest,
  UserCreateRequest,
  UserListParams,
  UserResponse,
  UserUpdateRequest,
} from '@/types/user'
import { del, get, post, put } from './request'

/**
 * 獲取使用者列表 API
 *
 * @param params - 查詢參數(分頁、篩選)
 * @returns 使用者列表響應(含分頁資訊)
 */
export async function getUserList(params: UserListParams = {}) {
  const response = await get<ApiResponse<PaginationResponse<UserResponse>>>('/v1/users', {
    params,
  })

  if (!response.data) {
    throw new Error('獲取使用者列表失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 根據 ID 獲取單一使用者 API
 *
 * @param id - 使用者 ID
 * @returns 使用者資料
 */
export async function getUserById(id: number): Promise<UserResponse> {
  const response = await get<ApiResponse<UserResponse>>(`/v1/users/${id}`)

  if (!response.data) {
    throw new Error('獲取使用者失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 建立新使用者 API（需要管理員權限）
 *
 * @param data - 使用者建立請求資料
 * @returns 新建立的使用者資料
 */
export async function createUser(data: UserCreateRequest): Promise<UserResponse> {
  const response = await post<ApiResponse<UserResponse>>('/v1/users', data)

  if (!response.data) {
    throw new Error('建立使用者失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 更新使用者資料 API（需要管理員權限或本人）
 *
 * @param id - 使用者 ID
 * @param data - 使用者更新請求資料
 * @returns 更新後的使用者資料
 */
export async function updateUser(id: number, data: UserUpdateRequest): Promise<UserResponse> {
  const response = await put<ApiResponse<UserResponse>>(`/v1/users/${id}`, data)

  if (!response.data) {
    throw new Error('更新使用者失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 刪除使用者 API（軟刪除，需要管理員權限）
 *
 * @param id - 使用者 ID
 */
export async function deleteUser(id: number): Promise<void> {
  await del<ApiResponse<{ message: string }>>(`/v1/users/${id}`)
}

/**
 * 分配角色給使用者 API（需要管理員權限）
 *
 * @param id - 使用者 ID
 * @param data - 角色分配請求資料
 * @returns 更新後的使用者資料
 */
export async function assignRoles(id: number, data: AssignRolesRequest): Promise<UserResponse> {
  const response = await post<ApiResponse<UserResponse>>(`/v1/users/${id}/roles`, data)

  if (!response.data) {
    throw new Error('分配角色失敗：無效的響應格式')
  }

  return response.data
}
