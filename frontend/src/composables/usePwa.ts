import { useRegisterSW } from 'virtual:pwa-register/vue'
import { onMounted, onUnmounted, ref } from 'vue'

export function usePwa() {
  // SW 更新通知 — 每小時檢查一次
  const {
    needRefresh,
    updateServiceWorker,
  } = useRegisterSW({
    immediate: true,
    onRegisteredSW(_swUrl, registration) {
      if (registration) {
        setInterval(() => {
          registration.update()
        }, 60 * 60 * 1000)
      }
    },
  })

  function applyUpdate() {
    updateServiceWorker()
  }

  function dismissUpdate() {
    needRefresh.value = false
  }

  // 安裝提示
  const canInstall = ref(false)
  const isIosSafari = ref(false)
  let deferredPrompt: Event | null = null

  // 偵測 iOS Safari（不支援 beforeinstallprompt）
  function detectIosSafari(): boolean {
    const ua = navigator.userAgent
    const isIos = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
    const isSafari = /Safari/.test(ua) && !/CriOS|FxiOS|OPiOS|EdgiOS|Chrome/.test(ua)
    // 已安裝為 PWA 時不顯示（standalone 模式）
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches
      || ('standalone' in window.navigator && (window.navigator as any).standalone)
    return isIos && isSafari && !isStandalone
  }

  function handleBeforeInstallPrompt(e: Event) {
    e.preventDefault()
    deferredPrompt = e
    canInstall.value = true
  }

  async function installApp() {
    if (!deferredPrompt) return
    const promptEvent = deferredPrompt as any
    promptEvent.prompt()
    const result = await promptEvent.userChoice
    if (result.outcome === 'accepted') {
      canInstall.value = false
    }
    deferredPrompt = null
  }

  function dismissInstall() {
    canInstall.value = false
    deferredPrompt = null
    isIosSafari.value = false
  }

  // 離線偵測
  const isOnline = ref(navigator.onLine)

  function handleOnline() {
    isOnline.value = true
  }

  function handleOffline() {
    isOnline.value = false
  }

  onMounted(() => {
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    // iOS Safari 無 beforeinstallprompt，改為顯示引導提示
    if (detectIosSafari()) {
      isIosSafari.value = true
    }
  })

  onUnmounted(() => {
    window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    // SW 更新
    needRefresh,
    applyUpdate,
    dismissUpdate,
    // 安裝提示
    canInstall,
    isIosSafari,
    installApp,
    dismissInstall,
    // 離線偵測
    isOnline,
  }
}
