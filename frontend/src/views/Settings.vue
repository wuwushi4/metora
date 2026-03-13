<script setup lang="ts">
import type { SettingsGroupResponse } from '@/types/settings'
import { NSpin, NTabPane, NTabs } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { getAllSettings } from '@/api/settings'
import AuthSettings from '@/components/settings/AuthSettings.vue'
import ChatSettings from '@/components/settings/ChatSettings.vue'
import RagSettings from '@/components/settings/RagSettings.vue'
import UploadSettings from '@/components/settings/UploadSettings.vue'
import { message } from '@/utils/message'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 狀態
const loading = ref(false)
const settings = ref<SettingsGroupResponse>({
  auth: [],
  rag: [],
  chat: [],
  upload: [],
})
const activeTab = ref('auth')

// 載入設定
async function loadSettings() {
  loading.value = true
  try {
    const response = await getAllSettings()
    settings.value = response
  }
  catch (error: any) {
    console.error('載入設定失敗:', error)
    message.error(error.message || t('settings.loadFailed'))
  }
  finally {
    loading.value = false
  }
}

// 處理設定更新
function handleSettingUpdated() {
  loadSettings() // 重新載入
}

// 頁面載入時獲取設定
onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="settings-page">
    <!-- 頁面標題 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          {{ t('settings.title') }}
        </h1>
        <p class="page-description">
          {{ t('settings.description') }}
        </p>
      </div>
    </div>

    <!-- 設定分頁 -->
    <div class="settings-content">
      <NSpin :show="loading">
        <NTabs v-model:value="activeTab" type="line" animated>
          <NTabPane name="auth" :tab="`🔐 ${t('settings.tabs.auth')}`">
            <AuthSettings
              :settings="settings.auth"
              @updated="handleSettingUpdated"
            />
          </NTabPane>

          <NTabPane name="rag" :tab="`🤖 ${t('settings.tabs.rag')}`">
            <RagSettings
              :settings="settings.rag"
              @updated="handleSettingUpdated"
            />
          </NTabPane>

          <NTabPane name="chat" :tab="`💬 ${t('settings.tabs.agent')}`">
            <ChatSettings
              :settings="settings.chat"
              @updated="handleSettingUpdated"
            />
          </NTabPane>

          <NTabPane name="upload" :tab="`📁 ${t('settings.tabs.upload')}`">
            <UploadSettings
              :settings="settings.upload"
              @updated="handleSettingUpdated"
            />
          </NTabPane>
        </NTabs>
      </NSpin>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e5e7eb;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.page-description {
  margin: 8px 0 0;
  font-size: 0.9375rem;
  color: #6b7280;
}

.settings-content {
  margin-top: 24px;
}

@media (max-width: 768px) {
  .settings-page {
    padding: 16px;
  }

  .page-title {
    font-size: 1.5rem;
  }
}
</style>
