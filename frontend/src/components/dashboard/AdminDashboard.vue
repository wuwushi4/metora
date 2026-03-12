<script setup lang="ts">
import type { AdminDashboardStats, TimeRange } from '@/types/dashboard'
import {
  NotificationsOutline as BellIcon,
  BarChartOutline as ChartIcon,
  ChatbubbleEllipsesOutline as ChatIcon,
  RefreshOutline as RefreshIcon,
  ThumbsDownOutline as ThumbsDownIcon,
  ThumbsUpOutline as ThumbsUpIcon,
} from '@vicons/ionicons5'
import { NButton, NCard, NGrid, NGridItem, NIcon, NSelect, NSpin } from 'naive-ui'
import { markRaw, onBeforeUnmount, onMounted, ref } from 'vue'
import { getAdminDashboardStats } from '@/api/dashboard'
import { useAuthStore } from '@/stores/auth'
import IssueTagList from './IssueTagList.vue'
import StatCard from './StatCard.vue'

const authStore = useAuthStore()
const loading = ref(false)
const stats = ref<AdminDashboardStats | null>(null)
const selectedTimeRange = ref<TimeRange>('all')

// 用於取消 API 請求的 AbortController
const abortController = ref<AbortController | null>(null)

const timeRangeOptions = [
  { label: '今日', value: 'today' },
  { label: '本週', value: 'this_week' },
  { label: '本月', value: 'this_month' },
  { label: '最近 7 天', value: 'last_7_days' },
  { label: '最近 30 天', value: 'last_30_days' },
  { label: '全部', value: 'all' },
]

async function fetchStats() {
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
    const response = await getAdminDashboardStats(selectedTimeRange.value)
    stats.value = response.data ?? null
  }
  catch (error: any) {
    // 忽略主動取消的錯誤
    if (error.name === 'AbortError' || error.name === 'CanceledError') {
      return
    }

    // ⭐ 只在非登出狀態下輸出錯誤
    if (!authStore.isLoggingOut && authStore.isAuthenticated) {
      console.error('獲取統計資料失敗:', error)
    }
  }
  finally {
    loading.value = false
  }
}

function handleTimeRangeChange() {
  fetchStats()
}

function handleRefresh() {
  fetchStats()
}

onMounted(() => {
  fetchStats()
})

// ⭐ 方案 C: 組件銷毀時取消請求
onBeforeUnmount(() => {
  if (abortController.value) {
    abortController.value.abort()
  }
})
</script>

<template>
  <div class="admin-dashboard">
    <!-- 標題列 -->
    <div class="dashboard-header">
      <div>
        <h1 class="dashboard-title">
          系統管理員儀表板
        </h1>
        <p class="dashboard-subtitle">
          系統運營監控與 AI 品質分析
        </p>
      </div>
      <div class="header-actions">
        <NSelect
          v-model:value="selectedTimeRange"
          :options="timeRangeOptions"
          style="width: 160px"
          @update:value="handleTimeRangeChange"
        />
        <NButton @click="handleRefresh">
          <template #icon>
            <NIcon><RefreshIcon /></NIcon>
          </template>
          刷新
        </NButton>
      </div>
    </div>

    <NSpin :show="loading">
      <div v-if="stats" class="dashboard-content">
        <!-- 聊天互動指標 -->
        <div class="section">
          <h2 class="section-title">
            聊天互動指標
          </h2>
          <NGrid cols="1 s:2 m:3" responsive="screen" :x-gap="20" :y-gap="20">
            <NGridItem>
              <StatCard
                label="總對話數"
                :value="stats.chat_stats.total_sessions"
                suffix="個"
                :icon="markRaw(ChatIcon)"
                color="linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="總訊息數"
                :value="stats.chat_stats.total_messages"
                suffix="則"
                :icon="markRaw(ChatIcon)"
                color="linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="日均訊息量"
                :value="stats.chat_stats.daily_avg_messages"
                suffix="則/天"
                :icon="markRaw(ChartIcon)"
                color="linear-gradient(135deg, #10b981 0%, #34d399 100%)"
              />
            </NGridItem>
            <!-- <NGridItem>
              <StatCard
                label="RAG 對話數"
                :value="stats.chat_stats.graph_type_distribution.rag_graph || 0"
                suffix="個"
                :icon="markRaw(ChatIcon)"
                color="linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)"
              />
            </NGridItem> -->
          </NGrid>
        </div>

        <!-- Graph 類型分布 -->
        <div class="section">
          <h2 class="section-title">
            Agent 類型分布
          </h2>
          <NGrid cols="1 s:2 m:3" responsive="screen" :x-gap="20" :y-gap="20">
            <NGridItem>
              <StatCard
                label="基礎對話"
                :value="stats.chat_stats.graph_type_distribution.base_graph || 0"
                suffix="個"
                :icon="markRaw(ChatIcon)"
                color="linear-gradient(135deg, #64748b 0%, #94a3b8 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="RAG 對話"
                :value="stats.chat_stats.graph_type_distribution.rag_graph || 0"
                suffix="個"
                :icon="markRaw(ChatIcon)"
                color="linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="法規查詢"
                :value="stats.chat_stats.graph_type_distribution.regulation_graph || 0"
                suffix="個"
                :icon="markRaw(ChatIcon)"
                color="linear-gradient(135deg, #ec4899 0%, #f472b6 100%)"
              />
            </NGridItem>
          </NGrid>
        </div>

        <!-- AI 品質反饋指標 -->
        <div class="section">
          <h2 class="section-title">
            AI 品質反饋指標
          </h2>
          <NGrid cols="1 s:2 m:5" responsive="screen" :x-gap="20" :y-gap="20">
            <NGridItem>
              <StatCard
                label="讚數 👍"
                :value="stats.feedback_stats.thumbs_up_count"
                suffix="個"
                :icon="markRaw(ThumbsUpIcon)"
                color="linear-gradient(135deg, #10b981 0%, #34d399 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="踩數 👎"
                :value="stats.feedback_stats.thumbs_down_count"
                suffix="個"
                :icon="markRaw(ThumbsDownIcon)"
                color="linear-gradient(135deg, #ef4444 0%, #f87171 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="讚比例"
                :value="`${stats.feedback_stats.thumbs_up_rate}%`"
                :icon="markRaw(ChartIcon)"
                color="linear-gradient(135deg, #14b8a6 0%, #5eead4 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="反饋率"
                :value="`${stats.feedback_stats.feedback_rate}%`"
                :icon="markRaw(ChartIcon)"
                color="linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)"
              />
            </NGridItem>
            <NGridItem>
              <StatCard
                label="待審查 🔔"
                :value="stats.feedback_stats.pending_review_count"
                suffix="個"
                :icon="markRaw(BellIcon)"
                color="linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)"
                :highlight="true"
              />
            </NGridItem>
          </NGrid>
        </div>

        <!-- 常見問題標籤 -->
        <div class="section">
          <NCard title="常見問題標籤 Top 10" :bordered="false" class="dashboard-card">
            <IssueTagList :tags="stats.feedback_stats.top_issue_tags" />
          </NCard>
        </div>
      </div>
    </NSpin>
  </div>
</template>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 標題列 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.dashboard-title {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.dashboard-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 內容區域 */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* 區塊 */
.section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
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

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .dashboard-title {
    font-size: 1.5rem;
  }

  .dashboard-subtitle {
    font-size: 0.875rem;
  }

  .section-title {
    font-size: 1.125rem;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .header-actions :deep(.n-select) {
    width: 140px !important;
  }

  .dashboard-content {
    gap: 24px;
  }
}
</style>
