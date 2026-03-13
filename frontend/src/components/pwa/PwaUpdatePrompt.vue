<script setup lang="ts">
import { NAlert, NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'

defineProps<{
  show: boolean
}>()

defineEmits<{
  update: []
  dismiss: []
}>()

const { t } = useI18n()
</script>

<template>
  <Transition name="slide-up">
    <div v-if="show" class="pwa-update-prompt">
      <NAlert type="info" :bordered="false">
        <template #header>
          {{ t('pwa.update.title') }}
        </template>
        <div class="update-actions">
          <NButton size="small" type="primary" @click="$emit('update')">
            {{ t('pwa.update.updateButton') }}
          </NButton>
          <NButton size="small" quaternary @click="$emit('dismiss')">
            {{ t('pwa.update.dismissButton') }}
          </NButton>
        </div>
      </NAlert>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-update-prompt {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 9999;
  max-width: 320px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  overflow: hidden;
}

.update-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

@media (max-width: 640px) {
  .pwa-update-prompt {
    left: 16px;
    right: 16px;
    max-width: none;
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
