<script setup lang="ts">
import type { SettingResponse } from '@/types/settings'
import {
  NButton,
  NFormItem,
  NInput,
  NInputNumber,
  NSwitch,
  NTag,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'

// Props
const props = defineProps<{
  setting: SettingResponse
}>()

// Emits
const emit = defineEmits<{
  update: [key: string, value: any]
}>()


// 本地值
const localValue = ref(props.setting.value)

// 檢查是否有變更
const hasChanges = computed(() => {
  return localValue.value !== props.setting.value
})

// 監聽 prop 變化
watch(
  () => props.setting.value,
  (newVal) => {
    localValue.value = newVal
  },
)

// 處理儲存
function handleSave() {
  emit('update', props.setting.setting_key, localValue.value)
}

// 處理取消
function handleReset() {
  localValue.value = props.setting.value
}
</script>

<template>
  <NFormItem>
    <template #label>
      <div class="flex items-center gap-2">
        <span>{{ setting.display_name }}</span>
        <NTag v-if="setting.requires_restart" type="warning" size="small">
          {{ $t('settings.requiresRestart') }}
        </NTag>
      </div>
    </template>

    <div class="flex items-center gap-3 w-full">
      <!-- Boolean 類型 -->
      <NSwitch
        v-if="setting.value_type === 'bool'"
        v-model:value="localValue"
        class="flex-shrink-0"
      />

      <!-- Int/Float 類型 -->
      <NInputNumber
        v-else-if="setting.value_type === 'int' || setting.value_type === 'float'"
        v-model:value="localValue"
        :min="setting.min_value"
        :max="setting.max_value"
        :step="setting.value_type === 'int' ? 1 : 0.1"
        class="flex-1"
      />

      <!-- String 類型 -->
      <NInput
        v-else
        v-model:value="localValue"
        class="flex-1"
      />

      <!-- 操作按鈕 -->
      <div v-if="hasChanges" class="flex gap-2 flex-shrink-0">
        <NButton type="primary" size="small" @click="handleSave">
          {{ $t('common.actions.save') }}
        </NButton>
        <NButton size="small" @click="handleReset">
          {{ $t('common.actions.cancel') }}
        </NButton>
      </div>
    </div>

    <!-- 說明文字 -->
    <template #feedback>
      <span class="text-xs text-gray-500">{{ setting.description }}</span>
    </template>
  </NFormItem>
</template>

<style scoped>
/* 確保表單項目正確對齊 */
.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-3 {
  gap: 0.75rem;
}

.w-full {
  width: 100%;
}

.flex-1 {
  flex: 1;
}

.flex-shrink-0 {
  flex-shrink: 0;
}

.text-xs {
  font-size: 0.75rem;
}

.text-gray-500 {
  color: #6b7280;
}
</style>
