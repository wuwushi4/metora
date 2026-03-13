import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { dateEnUS, dateZhTW, enUS, zhTW } from 'naive-ui'

/**
 * 語言切換 composable
 * 同步切換 vue-i18n locale + Naive UI locale + localStorage
 */
export function useLocale() {
  const { locale } = useI18n()

  const currentLocale = computed(() => locale.value)

  const naiveLocale = computed(() => {
    return locale.value === 'en' ? enUS : zhTW
  })

  const naiveDateLocale = computed(() => {
    return locale.value === 'en' ? dateEnUS : dateZhTW
  })

  function setLocale(lang: string) {
    locale.value = lang
    localStorage.setItem('locale', lang)
    document.documentElement.setAttribute('lang', lang)
  }

  function toggleLocale() {
    const next = locale.value === 'zh-TW' ? 'en' : 'zh-TW'
    setLocale(next)
  }

  return {
    currentLocale,
    naiveLocale,
    naiveDateLocale,
    setLocale,
    toggleLocale,
  }
}
