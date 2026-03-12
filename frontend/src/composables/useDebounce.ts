import type { Ref } from 'vue'
import { ref, watch } from 'vue'

export function useDebouncedRef<T>(value: Ref<T> | T, delay = 300) {
  const originalValue = ref(value) as Ref<T>
  const debouncedValue = ref(value) as Ref<T>
  let timeout: ReturnType<typeof setTimeout>

  watch(originalValue, (newValue) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      debouncedValue.value = newValue
    }, delay)
  })

  return { originalValue, debouncedValue }
}
