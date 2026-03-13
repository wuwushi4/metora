<script setup lang="ts">
import type { UserDashboardInfo } from '@/types/dashboard'
import { ChatbubbleEllipsesOutline as ChatIcon, FolderOpenOutline as FolderIcon } from '@vicons/ionicons5'
import { NButton, NCard, NGrid, NGridItem, NIcon, NSpin } from 'naive-ui'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getUserDashboardInfo } from '@/api/dashboard'
import { useAuthStore } from '@/stores/auth'
import StatCard from './StatCard.vue'
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const dashboardInfo = ref<UserDashboardInfo | null>(null)

// 用於取消 API 請求的 AbortController
const abortController = ref<AbortController | null>(null)

async function fetchDashboardInfo() {
  // ⭐ 方案 B: 檢查是否正在登出或未登入
  if (!authStore.isAuthenticated || authStore.isLoggingOut) {
    return // 直接返回,不發送請求
  }

  // ⭐ 方案 C: 取消之前的請求
  if (abortController.value) {
    abortController.value.abort()
  }

  // 建立新的 AbortController
  abortController.value = new AbortController()

  loading.value = true
  try {
    const response = await getUserDashboardInfo()
    dashboardInfo.value = response.data ?? null
  }
  catch (error: any) {
    // 忽略主動取消的錯誤
    if (error.name === 'AbortError' || error.name === 'CanceledError') {
      return
    }

    // ⭐ 只在非登出狀態下輸出錯誤
    if (!authStore.isLoggingOut && authStore.isAuthenticated) {
      console.error('獲取儀表板資訊失敗:', error)
    }
  }
  finally {
    loading.value = false
  }
}

function navigateTo(path: string) {
  router.push(path)
}

onMounted(() => {
  fetchDashboardInfo()
})

// ⭐ 方案 C: 組件銷毀時取消請求
onBeforeUnmount(() => {
  if (abortController.value) {
    abortController.value.abort()
  }
})
</script>

<template>
  <div class="user-dashboard">
    <NSpin :show="loading">
      <div v-if="dashboardInfo" class="dashboard-content">
        <!-- 歡迎區塊 -->
        <div class="welcome-section">
          <h1 class="welcome-title">
            {{ dashboardInfo.welcome_message }}
          </h1>
          <p class="welcome-subtitle">
            {{ $t('dashboard.user.subtitle') }}
          </p>
        </div>

        <!-- 快速操作 -->
        <NCard :title="$t('dashboard.user.quickActions')" :bordered="false" class="dashboard-card">
          <div class="quick-actions">
            <NButton type="primary" size="large" @click="navigateTo('/chat')">
              <template #icon>
                <NIcon><ChatIcon /></NIcon>
              </template>
              {{ $t('dashboard.user.startChat') }}
            </NButton>
            <NButton size="large" @click="navigateTo('/collections')">
              <template #icon>
                <NIcon><FolderIcon /></NIcon>
              </template>
              {{ $t('dashboard.user.myCollections') }}
            </NButton>
          </div>
        </NCard>

        <!-- 基本統計 -->
        <NCard :title="$t('dashboard.user.myStats')" :bordered="false" class="dashboard-card" style="margin-top: 20px;">
          <NGrid cols="1 s:2" responsive="screen" :x-gap="20" :y-gap="20">
            <NGridItem>
              <StatCard
                :label="$t('dashboard.user.mySessions')"
                :value="dashboardInfo.basic_stats.total_sessions"
                :icon="ChatIcon"
                color="linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                :label="$t('dashboard.user.myMessages')"
                :value="dashboardInfo.basic_stats.total_messages"
                :icon="ChatIcon"
                color="linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)"
              />
            </NGridItem>
          </NGrid>
        </NCard>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.user-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 歡迎區塊 */
.welcome-section {
  padding: 20px 0;
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

/* 快速操作 */
.quick-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .quick-actions {
    flex-direction: column;
  }
}
</style>
