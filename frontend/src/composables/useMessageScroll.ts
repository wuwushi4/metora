/**
 * 訊息自動滾動 Composable
 * 處理訊息列表的自動滾動邏輯
 */
import { nextTick, ref } from 'vue'

export function useMessageScroll() {
  const scrollContainer = ref<HTMLElement | null>(null)
  const shouldAutoScroll = ref(true)

  /**
   * 滾動到底部
   *
   * @param smooth 是否平滑滾動
   */
  async function scrollToBottom(smooth = true) {
    await nextTick()

    if (scrollContainer.value && shouldAutoScroll.value) {
      scrollContainer.value.scrollTo({
        top: scrollContainer.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      })
    }
  }

  /**
   * 處理滾動事件
   * 判斷使用者是否手動滾動到非底部位置
   */
  function handleScroll() {
    if (!scrollContainer.value)
      return

    const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value
    const distanceToBottom = scrollHeight - scrollTop - clientHeight

    // 如果距離底部小於 50px,視為在底部
    shouldAutoScroll.value = distanceToBottom < 50
  }

  /**
   * 強制啟用自動滾動並滾動到底部
   */
  async function enableAutoScrollAndScroll() {
    shouldAutoScroll.value = true
    await scrollToBottom(true)
  }

  return {
    scrollContainer,
    shouldAutoScroll,
    scrollToBottom,
    handleScroll,
    enableAutoScrollAndScroll,
  }
}
