<script setup lang="ts">
import type { Component } from 'vue'
import { NBadge, NIcon } from 'naive-ui'
import { computed } from 'vue'

interface Props {
  label: string
  value: number | string
  suffix?: string
  icon: Component
  color: string
  highlight?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  suffix: '',
  highlight: false,
})

const cardStyle = computed(() => ({
  '--card-color': props.color,
}))
</script>

<template>
  <div class="stat-card" :style="cardStyle">
    <div class="stat-header">
      <div class="stat-icon">
        <NIcon size="24" :component="icon" />
      </div>
      <NBadge v-if="highlight && typeof value === 'number' && value > 0" :value="value" type="error" />
    </div>
    <div class="stat-body">
      <div class="stat-value">
        {{ value }}<span v-if="suffix" class="stat-suffix">{{ suffix }}</span>
      </div>
      <div class="stat-label">
        {{ label }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--card-color);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--card-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}

.stat-suffix {
  font-size: 1rem;
  font-weight: 400;
  color: #6b7280;
  margin-left: 4px;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
  }

  .stat-header {
    margin-bottom: 12px;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .stat-suffix {
    font-size: 0.875rem;
  }
}
</style>
