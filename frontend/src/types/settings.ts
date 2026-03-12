/**
 * 系統設定類型定義
 */

/**
 * 設定值類型
 */
export type SettingValueType = 'int' | 'float' | 'bool' | 'string' | 'array'

/**
 * 設定分類
 */
export type SettingCategory = 'auth' | 'rag' | 'chat' | 'upload'

/**
 * 單一設定回應 (對應後端 SettingResponse)
 */
export interface SettingResponse {
  id: number
  category: SettingCategory
  setting_key: string
  value: any
  value_type: SettingValueType
  default_value?: any
  display_name: string
  description?: string
  min_value?: number
  max_value?: number
  requires_restart: boolean
  is_sensitive: boolean
  updated_at?: string
  updated_by?: number
}

/**
 * 設定分組回應 (對應後端 SettingsGroupResponse)
 */
export interface SettingsGroupResponse {
  auth: SettingResponse[]
  rag: SettingResponse[]
  chat: SettingResponse[]
  upload: SettingResponse[]
}

/**
 * 更新設定請求 (對應後端 SettingUpdate)
 */
export interface SettingUpdateRequest {
  value: any
}
