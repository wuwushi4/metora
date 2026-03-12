/**
 * 使用者資料型別定義（符合後端 UserInfo schema）
 */
export interface User {
  /** 使用者 ID */
  id: number
  /** 使用者帳號 */
  username: string
  /** 電子郵件 */
  email: string
  /** 真實姓名 */
  full_name?: string
  /** 頭像 URL */
  avatar_url?: string
  /** 是否啟用 */
  is_active: boolean
  /** 是否為超級使用者 */
  is_superuser: boolean
  /** 使用者角色列表 */
  roles?: string[]
}

/**
 * Token 響應資料（符合後端 TokenResponse schema）
 */
export interface TokenResponse {
  /** 訪問令牌 */
  access_token: string
  /** 刷新令牌 */
  refresh_token: string
  /** Token 類型（通常為 "bearer"） */
  token_type: string
}

/**
 * 登入響應資料（符合後端 LoginResponse schema）
 */
export interface LoginResponse {
  /** 使用者資訊（tokens 在 httpOnly cookie 中） */
  user: User
}

/**
 * 使用者響應（符合後端 UserResponse schema）
 * 用於 Users API 的響應資料
 */
export interface UserResponse {
  /** 使用者 ID */
  id: number
  /** 使用者帳號 */
  username: string
  /** 電子郵件 */
  email: string
  /** 真實姓名 */
  full_name?: string
  /** 是否啟用 */
  is_active: boolean
  /** 是否為超級使用者 */
  is_superuser: boolean
  /** 建立時間 */
  created_at: string
  /** 使用者角色列表 */
  roles: string[]
}

/**
 * 建立使用者請求（符合後端 UserCreate schema）
 */
export interface UserCreateRequest {
  /** 使用者名稱 */
  username: string
  /** 電子郵件 */
  email: string
  /** 密碼 */
  password: string
  /** 真實姓名 */
  full_name?: string
  /** 角色列表 */
  roles?: string[]
}

/**
 * 更新使用者請求（符合後端 UserUpdate schema）
 */
export interface UserUpdateRequest {
  /** 電子郵件 */
  email?: string
  /** 真實姓名 */
  full_name?: string
  /** 是否啟用 */
  is_active?: boolean
}

/**
 * 使用者列表查詢參數（符合後端 UserListParams schema）
 */
export interface UserListParams {
  /** 頁碼（從 1 開始） */
  page?: number
  /** 每頁筆數（1-100） */
  page_size?: number
  /** 使用者名稱（模糊搜尋） */
  username?: string
  /** 電子郵件（模糊搜尋） */
  email?: string
  /** 是否啟用（精確搜尋） */
  is_active?: boolean
  /** 角色（精確搜尋） */
  role?: string
}

/**
 * 分配角色請求（符合後端 AssignRolesRequest schema）
 */
export interface AssignRolesRequest {
  /** 角色名稱列表 */
  roles: string[]
}

/**
 * 修改密碼請求（符合後端 ChangePasswordRequest schema）
 */
export interface ChangePasswordRequest {
  /** 舊密碼 */
  old_password: string
  /** 新密碼 */
  new_password: string
}
