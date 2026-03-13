<script setup lang="ts">
import { DownloadOutline, ShareOutline } from '@vicons/ionicons5'
import { NButton, NIcon } from 'naive-ui'
import { useI18n } from 'vue-i18n'

defineProps<{
  show: boolean
  isIos?: boolean
}>()

defineEmits<{
  install: []
  dismiss: []
}>()

const { t } = useI18n()
</script>

<template>
  <Transition name="slide-up">
    <div v-if="show" class="pwa-install-prompt">
      <!-- iOS Safari 引導模式 -->
      <template v-if="isIos">
        <div class="install-content">
          <NIcon :size="20" :component="ShareOutline" class="install-icon" />
          <div class="install-text-group">
            <span class="install-text">{{ t('pwa.install.title') }}</span>
            <span class="install-hint">
              {{ t('pwa.install.iosMessage') }}
            </span>
          </div>
        </div>
        <div class="install-actions">
          <NButton size="small" quaternary @click="$emit('dismiss')">
            {{ t('pwa.install.dismissButton') }}
          </NButton>
        </div>
      </template>

      <!-- 標準安裝提示（Android / Desktop） -->
      <template v-else>
        <div class="install-content">
          <NIcon :size="20" :component="DownloadOutline" class="install-icon" />
          <span class="install-text">{{ t('pwa.install.title') }}</span>
        </div>
        <div class="install-actions">
          <NButton size="small" type="primary" @click="$emit('install')">
            {{ t('pwa.install.installButton') }}
          </NButton>
          <NButton size="small" quaternary @click="$emit('dismiss')">
            {{ t('pwa.install.dismissButton') }}
          </NButton>
        </div>
      </template>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-install-prompt {
  position: fixed;
  bottom: 16px;
  left: 16px;
  z-index: 9999;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 380px;
}

.install-content {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.install-icon {
  color: #0ea5e9;
  flex-shrink: 0;
  margin-top: 2px;
}

.install-text-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.install-text {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.install-hint {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.install-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .pwa-install-prompt {
    left: 12px;
    right: 12px;
    max-width: none;
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .install-actions {
    justify-content: flex-end;
  }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
