import type { ApiResponse } from '@/types/api'
import type {
  SettingResponse,
  SettingsGroupResponse,
  SettingUpdateRequest,
} from '@/types/settings'
/**
 * 系統設定 API 請求
 */
import { get, put } from './request'

/**
 * 獲取所有系統設定
 */
export async function getAllSettings(): Promise<SettingsGroupResponse> {
  const response = await get<ApiResponse<SettingsGroupResponse>>('/v1/admin/settings')

  if (!response.data) {
    throw new Error('獲取系統設定失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 獲取單一設定
 */
export async function getSetting(key: string): Promise<SettingResponse> {
  const response = await get<ApiResponse<SettingResponse>>(`/v1/admin/settings/${key}`)

  if (!response.data) {
    throw new Error('獲取設定失敗：無效的響應格式')
  }

  return response.data
}

/**
 * 更新單一設定
 */
export async function updateSetting(
  key: string,
  data: SettingUpdateRequest,
): Promise<SettingResponse> {
  const response = await put<ApiResponse<SettingResponse>>(
    `/v1/admin/settings/${key}`,
    data,
  )

  if (!response.data) {
    throw new Error('更新設定失敗：無效的響應格式')
  }

  return response.data
}
