<script setup lang="ts">
import { CloudOfflineOutline } from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'
import { useI18n } from 'vue-i18n'

defineProps<{
  show: boolean
}>()

const { t } = useI18n()
</script>

<template>
  <Transition name="slide-down">
    <div v-if="show" class="offline-indicator">
      <NIcon :size="16" :component="CloudOfflineOutline" />
      <span>{{ t('pwa.offline.message') }}</span>
    </div>
  </Transition>
</template>

<style scoped>
.offline-indicator {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10000;
  background: #fbbf24;
  color: #78350f;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}
</style>
