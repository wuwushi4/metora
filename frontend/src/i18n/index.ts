import { createI18n } from 'vue-i18n'
import zhTW from './locales/zh-TW.json'
import en from './locales/en.json'

/**
 * 偵測預設語系
 * 優先順序：localStorage > navigator.language > 'zh-TW'
 */
function detectLocale(): string {
  const stored = localStorage.getItem('locale')
  if (stored && ['zh-TW', 'en'].includes(stored)) {
    return stored
  }

  const browserLang = navigator.language
  if (browserLang.startsWith('en')) {
    return 'en'
  }

  return 'zh-TW'
}

const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: 'zh-TW',
  messages: {
    'zh-TW': zhTW,
    'en': en,
  },
})

export default i18n
