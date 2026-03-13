<script setup lang="ts">
import type { SettingResponse } from '@/types/settings'
import { NCard, NForm, NSpin } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { updateSetting } from '@/api/settings'
import { message } from '@/utils/message'
import SettingItem from './SettingItem.vue'

// Props
const props = defineProps<{
  settings: SettingResponse[]
}>()

// Emits
const emit = defineEmits<{
  updated: []
}>()

const { t } = useI18n()

// 狀態
const loading = ref(false)

// 處理設定更新
async function handleUpdate(key: string, value: any) {
  loading.value = true
  try {
    await updateSetting(key, { value })
    message.success(t('settings.updateSuccess'))
    emit('updated')
  }
  catch (error: any) {
    console.error('更新設定失敗:', error)
    message.error(error.message || t('settings.updateFailed'))
  }
  finally {
    loading.value = false
  }
}

// 檢查是否有需要重啟的設定
const hasRestartRequired = computed(() => {
  return props.settings.some(s => s.requires_restart)
})
</script>

<template>
  <div class="auth-settings">
    <NSpin :show="loading">
      <NCard v-if="hasRestartRequired" class="mb-4" size="small">
        <div class="text-orange-600 text-sm">
          ⚠️ {{ $t('settings.restartWarning') }}
        </div>
      </NCard>

      <NCard :title="$t('settings.authTitle')">
        <NForm label-placement="left" label-width="200" class="max-w-3xl">
          <SettingItem
            v-for="setting in settings"
            :key="setting.setting_key"
            :setting="setting"
            @update="handleUpdate"
          />
        </NForm>
      </NCard>
    </NSpin>
  </div>
</template>

<style scoped>
.auth-settings {
  padding: 16px;
}

.mb-4 {
  margin-bottom: 1rem;
}

.text-orange-600 {
  color: #ea580c;
}

.text-sm {
  font-size: 0.875rem;
}

.max-w-3xl {
  max-width: 48rem;
}
</style>
