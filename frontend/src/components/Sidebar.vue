<script setup lang="ts">
import type { MenuOption } from 'naive-ui'
import {
  BarChartOutline as AnalyticsIcon,
  ChatbubbleEllipsesOutline as ChatIcon,
  FolderOpenOutline as CollectionIcon,
  GridOutline as DashboardIcon,
  DocumentTextOutline as DocumentIcon,
  ConstructOutline as EngineeringIcon,
  ChatbubblesOutline as FeedbackIcon,
  HomeOutline as HomeIcon,
  FolderOutline as ProjectIcon,
  ReceiptOutline as RegulationIcon,
  SettingsOutline as SettingsIcon,
  PeopleOutline as UsersIcon,
} from '@vicons/ionicons5'
import { NIcon, NLayoutSider, NMenu } from 'naive-ui'

import { computed, h, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePermission } from '@/composables/usePermission'

const props = defineProps<{
  collapsed: boolean
  isMobile?: boolean
}>()

const route = useRoute()
const router = useRouter()
const { hasRole } = usePermission()

// 使用 markRaw 防止圖示元件被 reactive 化
const icons = {
  dashboard: markRaw(DashboardIcon),
  home: markRaw(HomeIcon),
  project: markRaw(ProjectIcon),
  analytics: markRaw(AnalyticsIcon),
  document: markRaw(DocumentIcon),
  collections: markRaw(CollectionIcon),
  regulations: markRaw(RegulationIcon),
  chat: markRaw(ChatIcon),
  users: markRaw(UsersIcon),
  feedbacks: markRaw(FeedbackIcon),
  settings: markRaw(SettingsIcon),
  engineering: markRaw(EngineeringIcon),
}

// 行動端收合寬度為 0（完全隱藏），桌面端為 64（顯示圖示）
const siderCollapsedWidth = computed(() => props.isMobile ? 0 : 64)

// 選單項目 - 加入分組標籤和權限過濾
const menuOptions = computed<MenuOption[]>(() => {
  const options: MenuOption[] = [
    {
      type: 'group',
      label: '主要功能',
      key: 'main-group',
      children: [
        {
          label: '儀表板',
          key: 'dashboard',
          icon: () => h(NIcon, null, { default: () => h(icons.dashboard) }),
        },
        // {
        //   label: '首頁',
        //   key: 'home',
        //   icon: () => h(NIcon, null, { default: () => h(icons.home) }),
        // },
        {
          label: 'Agent Chat',
          key: 'chat',
          icon: () => h(NIcon, null, { default: () => h(icons.chat) }),
        },
      ],
    },
    {
      type: 'group',
      label: '資料管理',
      key: 'data-group',
      children: [
        {
          label: 'Collection 管理',
          key: 'collections',
          icon: () => h(NIcon, null, { default: () => h(icons.collections) }),
        },
        {
          label: '法規管理',
          key: 'regulations',
          icon: () => h(NIcon, null, { default: () => h(icons.regulations) }),
        },
        {
          label: '反饋記錄管理',
          key: 'feedbacks',
          icon: () => h(NIcon, null, { default: () => h(icons.feedbacks) }),
        },
        // {
        //   label: '專案管理',
        //   key: 'projects',
        //   icon: () => h(NIcon, null, { default: () => h(icons.project) }),
        // },
        // {
        //   label: '資料分析',
        //   key: 'analytics',
        //   icon: () => h(NIcon, null, { default: () => h(icons.analytics) }),
        // },
        // {
        //   label: '文件中心',
        //   key: 'documents',
        //   icon: () => h(NIcon, null, { default: () => h(icons.document) }),
        // },
      ],
    },
    {
      type: 'group',
      label: '資料工程',
      key: 'engineering-group',
      children: [
        {
          label: '法規爬蟲作業',
          key: 'law-processing',
          icon: () => h(NIcon, null, { default: () => h(icons.engineering) }),
        },
      ],
    },
  ]

  // 只有 admin 可以看到系統設定
  if (hasRole('admin')) {
    options.push({
      type: 'group',
      label: '系統設定',
      key: 'system-group',
      children: [
        {
          label: '使用者管理',
          key: 'users',
          icon: () => h(NIcon, null, { default: () => h(icons.users) }),
        },
        {
          label: '系統設定',
          key: 'settings',
          icon: () => h(NIcon, null, { default: () => h(icons.settings) }),
        },
      ],
    })
  }

  return options
})

// 當前選中的選單項目
const activeKey = computed(() => {
  const name = route.name as string
  return name?.toLowerCase() || 'dashboard'
})

// 處理選單選擇
function handleMenuSelect(key: string) {
  // 忽略分隔線和父級選單
  if (key.startsWith('divider') || key.endsWith('-group')) {
    return
  }

  // 導航到對應路由
  if (key === 'dashboard') {
    router.push('/')
  }
  else {
    router.push(`/${key}`)
  }
}
</script>

<template>
  <NLayoutSider
    bordered
    :collapsed="collapsed"
    collapse-mode="width"
    :collapsed-width="siderCollapsedWidth"
    :width="240"
    :native-scrollbar="false"
    class="sidebar-container"
  >
    <div class="sidebar-content">
      <NMenu
        :value="activeKey"
        :collapsed="collapsed"
        :collapsed-width="siderCollapsedWidth"
        :collapsed-icon-size="20"
        :options="menuOptions"
        :indent="20"
        :root-indent="20"
        class="sidebar-menu"
        @update:value="handleMenuSelect"
      />
    </div>
  </NLayoutSider>
</template>

<style scoped>
.sidebar-container {
  height: 100%;
  background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
  border-right: 1px solid #e5e7eb;
}

.sidebar-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-menu {
  flex: 1;
  padding: 12px 8px;
  background: transparent;
}

/* 自訂選單樣式 */
:deep(.n-menu-item) {
  margin: 2px 0;
  border-radius: 8px;
  height: 44px;
  transition: all 0.2s ease;
}

:deep(.n-menu-item:hover) {
  background-color: #f3f4f6 !important;
}

:deep(.n-menu-item.n-menu-item--selected) {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
  color: #0ea5e9 !important;
  font-weight: 600;
  box-shadow: 0 1px 2px 0 rgba(14, 165, 233, 0.1);
}

:deep(.n-menu-item.n-menu-item--selected .n-menu-item-content-header) {
  color: #0ea5e9 !important;
}

:deep(.n-menu-item-content) {
  padding-left: 12px !important;
}

/* 圖示樣式 */
:deep(.n-menu-item-content__icon) {
  margin-right: 12px;
  font-size: 20px;
  transition: transform 0.2s ease;
}

:deep(.n-menu-item:hover .n-menu-item-content__icon) {
  transform: scale(1.1);
}

/* 分組標題樣式 */
:deep(.n-menu-item-group-title) {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
  padding: 16px 20px 8px;
  margin-top: 8px;
}

:deep(.n-menu-item-group:first-child .n-menu-item-group-title) {
  margin-top: 0;
}

/* 收合模式樣式 */
:deep(.n-menu--collapsed) {
  padding: 12px 4px;
}

:deep(.n-menu--collapsed .n-menu-item) {
  justify-content: center;
  padding: 0;
}

:deep(.n-menu--collapsed .n-menu-item-content__icon) {
  margin-right: 0;
}

:deep(.n-menu--collapsed .n-menu-item-group-title) {
  display: none;
}

/* 動畫效果 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.sidebar-menu {
  animation: slideIn 0.3s ease-out;
}
</style>
