<script setup lang="ts">
import AdminDashboard from '@/components/dashboard/AdminDashboard.vue'
import UserDashboard from '@/components/dashboard/UserDashboard.vue'
import { usePermission } from '@/composables/usePermission'

const { hasRole } = usePermission()
</script>

<template>
  <div class="dashboard-container">
    <!-- 根據使用者角色顯示不同儀表板 -->
    <AdminDashboard v-if="hasRole('admin')" />
    <UserDashboard v-else />
  </div>
</template>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 歡迎區塊 */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

@media (max-width: 768px) {
  .dashboard-container {
    gap: 16px;
  }

  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .welcome-title {
    font-size: 1.5rem;
  }
}

.welcome-title {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.welcome-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

/* 統計卡片 */
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
  background: var(--card-gradient);
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
  background: var(--card-gradient);
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

/* 通用卡片 */
.dashboard-card {
  box-shadow:
    0 1px 3px 0 rgba(0, 0, 0, 0.1),
    0 1px 2px 0 rgba(0, 0, 0, 0.06);
  border-radius: 16px;
}

.dashboard-card :deep(.n-card-header) {
  padding: 20px 24px;
  font-weight: 600;
  font-size: 1.125rem;
}

/* 進度列表 */
.progress-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.progress-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.progress-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

/* 圖表佔位 */
.chart-placeholder {
  height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.chart-placeholder-text {
  color: #9ca3af;
  font-size: 0.875rem;
}

/* 快速操作 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-action-item:hover {
  background: #f3f4f6;
  transform: translateX(4px);
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

/* 活動列表 */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.activity-dot--success {
  background-color: #10b981;
}

.activity-dot--info {
  background-color: #0ea5e9;
}

.activity-dot--warning {
  background-color: #f59e0b;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-text {
  font-size: 0.875rem;
  color: #374151;
  margin: 0 0 4px 0;
  line-height: 1.4;
}

.activity-user {
  font-weight: 600;
  color: #111827;
}

.activity-time {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
}
</style>
