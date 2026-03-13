<script setup lang="ts">
import type { ChatSession, SessionCreateRequest } from '@/types/chat'
import { BookOutline as PromptIcon, CloseOutline as CloseIcon } from '@vicons/ionicons5'
import { NButton, NIcon, NLayout, NLayoutContent, NLayoutSider } from 'naive-ui'
import { useBreakpoints } from '@vueuse/core'
import { computed, onMounted, ref, watch } from 'vue'
import ChatConfig from '@/components/chat/ChatConfig.vue'
import ChatInterface from '@/components/chat/ChatInterface.vue'
import PromptPanel from '@/components/chat/PromptPanel.vue'
import SessionList from '@/components/chat/SessionList.vue'
import { useChatStore } from '@/stores/chat'
import { message } from '@/utils/message'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const chatStore = useChatStore()

// 配置彈窗
const showConfigModal = ref(false)

// Computed
const sessions = computed(() => chatStore.sessions)
const currentSession = computed(() => chatStore.currentSession)
const graphs = computed(() => chatStore.graphs)
const loadingStates = computed(() => chatStore.loadingStates)

// 是否收起側邊欄
const collapsed = ref(false)
// 是否收起右側提示詞面板
const rightCollapsed = ref(false)

// 行動端偵測
const breakpoints = useBreakpoints({ mobile: 768 })
const isMobile = breakpoints.smaller('mobile')

// 行動端預設收合右側面板
watch(isMobile, (mobile) => {
  if (mobile) {
    rightCollapsed.value = true
  }
}, { immediate: true })

// 右側面板寬度：行動端全寬，桌面端 380px
const promptSiderWidth = computed(() => isMobile.value ? window.innerWidth : 380)

// 處理選擇 Session
async function handleSelectSession(session: ChatSession) {
  try {
    await chatStore.switchSession(session.id)
  }
  catch (error) {
    console.error('切換對話失敗:', error)
  }
}

// 處理建立新 Session
function handleCreateSession() {
  showConfigModal.value = true
}

// 確認建立配置
async function handleConfirmConfig(config: SessionCreateRequest) {
  try {
    await chatStore.createNewSession(config)
  }
  catch (error) {
    console.error('建立對話失敗:', error)
  }
}

// 處理重命名 Session
async function handleRenameSession(sessionId: string, newTitle: string) {
  try {
    await chatStore.renameSession(sessionId, newTitle)
  }
  catch (error) {
    console.error('重命名失敗:', error)
  }
}

// 處理刪除 Session
async function handleDeleteSession(sessionId: string) {
  try {
    await chatStore.removeSession(sessionId)
  }
  catch (error) {
    console.error('刪除對話失敗:', error)
  }
}

// 初始化
onMounted(async () => {
  try {
    // 載入 Graphs
    await chatStore.loadGraphs()

    // 載入 Sessions
    await chatStore.loadSessions()

    // 如果有 Sessions,自動選擇第一個
    if (sessions.value.length > 0 && !currentSession.value) {
      const firstSession = sessions.value[0]
      if (firstSession) {
        await chatStore.switchSession(firstSession.id)
      }
    }
  }
  catch (error) {
    console.error('初始化失敗:', error)
    message.error(t('chat.loadFailed'))
  }
})
</script>

<template>
  <div class="chat-page">
    <NLayout has-sider class="chat-layout">
      <!-- 側邊欄 - Session 列表 -->
      <NLayoutSider
        :collapsed="collapsed"
        collapse-mode="width"
        :collapsed-width="0"
        :width="320"
        :native-scrollbar="false"
        bordered
        class="chat-sider"
        @collapse="collapsed = true"
        @expand="collapsed = false"
      >
        <SessionList
          :sessions="sessions"
          :current-session-id="currentSession?.id"
          :loading="loadingStates.sessions"
          @select="handleSelectSession"
          @create="handleCreateSession"
          @rename="handleRenameSession"
          @delete="handleDeleteSession"
        />
      </NLayoutSider>

      <!-- 自定義收合按鈕 -->
      <div
        class="collapse-trigger"
        :class="{ collapsed }"
        @click="collapsed = !collapsed"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          :class="{ 'rotate-180': collapsed }"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </div>

      <!-- 主要內容區 - 聊天介面 -->
      <NLayoutContent class="chat-content">
        <ChatInterface />
      </NLayoutContent>

      <!-- 右側邊欄 - 提示詞面板 -->
      <NLayoutSider
        :collapsed="rightCollapsed"
        collapse-mode="width"
        :collapsed-width="0"
        :width="promptSiderWidth"
        :native-scrollbar="false"
        bordered
        position="absolute"
        class="prompt-sider"
        @collapse="rightCollapsed = true"
        @expand="rightCollapsed = false"
      >
        <!-- 行動端關閉列 -->
        <div v-if="isMobile" class="mobile-panel-topbar">
          <span class="mobile-panel-topbar-title">{{ $t('chat.promptPanel') }}</span>
          <NButton size="tiny" quaternary @click="rightCollapsed = true">
            <template #icon>
              <NIcon :component="CloseIcon" />
            </template>
            {{ $t('common.actions.close') }}
          </NButton>
        </div>
        <PromptPanel />
      </NLayoutSider>

      <!-- 右側收合按鈕（桌面端） -->
      <div
        class="right-collapse-trigger desktop-only"
        :class="{ collapsed: rightCollapsed }"
        @click="rightCollapsed = !rightCollapsed"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          :class="{ 'rotate-180': !rightCollapsed }"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </div>

      <!-- 行動端：提示詞面板浮動開啟按鈕 -->
      <NButton
        v-if="isMobile && rightCollapsed"
        class="mobile-prompt-btn"
        type="primary"
        circle
        @click="rightCollapsed = false"
      >
        <template #icon>
          <NIcon :component="PromptIcon" />
        </template>
      </NButton>

      <!-- 行動端：右側面板遮罩 -->
      <div
        v-if="isMobile && !rightCollapsed"
        class="mobile-overlay"
        @click="rightCollapsed = true"
      />
    </NLayout>

    <!-- 建立對話配置彈窗 -->
    <ChatConfig
      v-model:show="showConfigModal"
      :graphs="graphs"
      :loading="loadingStates.creating"
      @confirm="handleConfirmConfig"
    />
  </div>
</template>

<style scoped>
.chat-page {
  height: calc(100vh - 128px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
}

@supports (height: 100dvh) {
  .chat-page {
    height: calc(100dvh - 128px);
  }
}

.chat-layout {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.chat-sider {
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(229, 231, 235, 0.8);
  border-left: none;
  border-right: 2px solid transparent;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)),
    linear-gradient(135deg, rgba(14, 165, 233, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
  background-origin: padding-box, border-box;
  background-clip: padding-box, border-box;
  box-shadow:
    2px 0 12px rgba(14, 165, 233, 0.08),
    2px 0 20px rgba(139, 92, 246, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.04);
  position: relative;
}

/* 頂部優雅裝飾線 */
.chat-sider::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    rgba(14, 165, 233, 0.6) 0%,
    rgba(99, 102, 241, 0.6) 50%,
    rgba(139, 92, 246, 0.6) 100%
  );
  box-shadow: 0 1px 3px rgba(14, 165, 233, 0.3);
}

.chat-content {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: transparent;
  position: relative;
}

/* 添加微妙的背景紋理 */
.chat-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 50%, rgba(14, 165, 233, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

/* 自定義收合按鈕 - 簡約線條風格 */
.collapse-trigger {
  position: absolute;
  left: 318px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 40px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e5e7eb;
  border-radius: 0 6px 6px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  transition: all 0.25s ease;
  box-shadow: 1px 0 3px rgba(0, 0, 0, 0.05);
}

.collapse-trigger:hover {
  background: rgba(239, 246, 255, 1);
  border-color: #0ea5e9;
  box-shadow: 1px 0 6px rgba(14, 165, 233, 0.15);
}

.collapse-trigger svg {
  color: #9ca3af;
  transition: all 0.25s ease;
}

.collapse-trigger:hover svg {
  color: #0ea5e9;
}

.collapse-trigger svg.rotate-180 {
  transform: rotate(180deg);
}

/* 當側邊欄收合時，調整按鈕位置 */
.collapse-trigger.collapsed {
  left: -2px;
  border-left: 1px solid #e5e7eb;
  border-radius: 0 6px 6px 0;
}

@media (max-width: 768px) {
  .collapse-trigger.collapsed {
    left: 8px;
  }
}

/* 右側提示詞面板 */
.prompt-sider {
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(229, 231, 235, 0.8);
  border-right: none;
  border-left: 2px solid transparent;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)),
    linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(14, 165, 233, 0.3) 100%);
  background-origin: padding-box, border-box;
  background-clip: padding-box, border-box;
  box-shadow:
    -2px 0 12px rgba(139, 92, 246, 0.08),
    -2px 0 20px rgba(14, 165, 233, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.04);
  position: relative;
  right: 0;
}

/* 頂部優雅裝飾線 */
.prompt-sider::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    rgba(139, 92, 246, 0.6) 0%,
    rgba(99, 102, 241, 0.6) 50%,
    rgba(14, 165, 233, 0.6) 100%
  );
  box-shadow: 0 1px 3px rgba(139, 92, 246, 0.3);
}

/* 右側收合按鈕 */
.right-collapse-trigger {
  position: absolute;
  right: 378px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 40px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e5e7eb;
  border-radius: 6px 0 0 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  transition: all 0.25s ease;
  box-shadow: -1px 0 3px rgba(0, 0, 0, 0.05);
}

.right-collapse-trigger:hover {
  background: rgba(243, 232, 255, 1);
  border-color: #8b5cf6;
  box-shadow: -1px 0 6px rgba(139, 92, 246, 0.15);
}

.right-collapse-trigger svg {
  color: #9ca3af;
  transition: all 0.25s ease;
}

.right-collapse-trigger:hover svg {
  color: #8b5cf6;
}

.right-collapse-trigger svg.rotate-180 {
  transform: rotate(180deg);
}

/* 當右側面板收合時，調整按鈕位置 */
.right-collapse-trigger.collapsed {
  right: -2px;
  border-right: 1px solid #e5e7eb;
  border-radius: 6px 0 0 6px;
}

/* 行動端面板頂部關閉列 */
.mobile-panel-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.06) 0%, rgba(14, 165, 233, 0.06) 100%);
}

.mobile-panel-topbar-title {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #6b7280;
}

/* 行動端浮動按鈕 - 提示詞面板 */
.mobile-prompt-btn {
  position: absolute;
  right: 16px;
  bottom: 80px;
  z-index: 50;
  width: 44px;
  height: 44px;
  box-shadow:
    0 4px 12px rgba(139, 92, 246, 0.3),
    0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 行動端遮罩層 */
.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 149;
  backdrop-filter: blur(2px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .chat-sider {
    position: absolute;
    z-index: 100;
    height: 100%;
    background: rgba(255, 255, 255, 0.98);
  }

  .chat-sider :deep(.n-layout-sider-scroll-container) {
    max-width: 85vw;
  }

  .collapse-trigger {
    left: calc(min(320px, 85vw) - 2px);
  }

  /* 行動端：右側面板覆蓋式（避開 Navbar 64px） */
  .prompt-sider {
    position: fixed !important;
    top: 64px;
    z-index: 150;
    height: calc(100vh - 64px) !important;
  }

  /* 展開時全寬覆蓋，移除裝飾性邊框 */
  .prompt-sider:not(.n-layout-sider--collapsed) {
    left: 0 !important;
    width: 100vw !important;
    background: #ffffff !important;
    background-image: none !important;
    border: none !important;
    box-shadow: none !important;
  }

  /* 桌面端收合按鈕在行動端隱藏 */
  .right-collapse-trigger.desktop-only {
    display: none;
  }
}
</style>
