import type { MessageApi, NotificationApi } from 'naive-ui'
import { createDiscreteApi } from 'naive-ui'

let messageApi: MessageApi | null = null
let notificationApi: NotificationApi | null = null

/**
 * 確保 API 已初始化（Lazy initialization）
 */
function ensureApi() {
  if (!messageApi) {
    const api = createDiscreteApi(['message', 'notification'], {
      messageProviderProps: {
        keepAliveOnHover: true,
        max: 3,
      },
      notificationProviderProps: {
        keepAliveOnHover: true,
        max: 3,
      },
    })
    messageApi = api.message
    notificationApi = api.notification
  }
}

/**
 * 全域 Message API（自動初始化）
 */
export const message = {
  info: (content: string, options?: any) => {
    ensureApi()
    return messageApi!.info(content, options)
  },
  success: (content: string, options?: any) => {
    ensureApi()
    return messageApi!.success(content, options)
  },
  warning: (content: string, options?: any) => {
    ensureApi()
    return messageApi!.warning(content, options)
  },
  error: (content: string, options?: any) => {
    ensureApi()
    return messageApi!.error(content, options)
  },
  loading: (content: string, options?: any) => {
    ensureApi()
    return messageApi!.loading(content, options)
  },
}

/**
 * 全域 Notification API（自動初始化）
 */
export const notification = {
  info: (options: any) => {
    ensureApi()
    return notificationApi!.info(options)
  },
  success: (options: any) => {
    ensureApi()
    return notificationApi!.success(options)
  },
  warning: (options: any) => {
    ensureApi()
    return notificationApi!.warning(options)
  },
  error: (options: any) => {
    ensureApi()
    return notificationApi!.error(options)
  },
}
