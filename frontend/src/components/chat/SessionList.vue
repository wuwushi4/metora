<script setup lang="ts">
import type { ChatSession } from '@/types/chat'
import { SearchOutline as SearchIcon } from '@vicons/ionicons5'
import { useDebounceFn } from '@vueuse/core'
import {
  NAutoComplete,
  NButton,
  NEmpty,
  NIcon,
  NInput,
  NList,
  NListItem,
  NModal,
  NPopconfirm,
  NSpace,
  NSpin,
  NTag,
  NText,
  NThing,
} from 'naive-ui'
import { computed, ref } from 'vue'
import { searchSessions } from '@/api/chat'
import { useSearchHistory } from '@/composables/useSearchHistory'
import { isSessionSearchResult } from '@/types/chat'
import { message } from '@/utils/message'
import { highlightKeyword } from '@/utils/searchHighlight'

const props = withDefaults(defineProps<Props>(), {
  currentSessionId: null,
  loading: false,
})
const emit = defineEmits<{
  select: [session: ChatSession]
  create: []
  rename: [sessionId: string, newTitle: string]
  delete: [sessionId: string]
}>()
// 常量定義
const SEARCH_DEBOUNCE_DELAY = 300
const SEARCH_PAGE_SIZE = 50

interface Props {
  sessions: ChatSession[]
  currentSessionId?: string | null
  loading?: boolean
}

// 重命名相關狀態
const showRenameModal = ref(false)
const renamingSession = ref<ChatSession | null>(null)
const newTitle = ref('')

// 搜尋相關狀態
const searchQuery = ref('')
const searchResults = ref<ChatSession[]>([])
const isSearching = ref(false)

// 搜尋歷史
const { history, addHistory } = useSearchHistory()

// 判斷是否為當前 Session
function isCurrentSession(sessionId: string): boolean {
  return props.currentSessionId === sessionId
}

// 格式化 Agent 類型標籤
function getGraphTypeLabel(graphType: string): string {
  switch (graphType) {
    case 'base_graph':
      return '通用助理'
    case 'rag_graph':
      return '知識專家'
    case 'regulation_graph':
      return '法規顧問'
    default:
      return graphType
  }
}

// 取得 Agent 類型標籤顏色
function getGraphTypeColor(graphType: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  switch (graphType) {
    case 'base_graph':
      return 'default'
    case 'rag_graph':
      return 'info'
    case 'regulation_graph':
      return 'success'
    default:
      return 'default'
  }
}

// 格式化時間
function formatTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小於 1 分鐘
  if (diff < 60 * 1000) {
    return '剛剛'
  }

  // 小於 1 小時
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes} 分鐘前`
  }

  // 小於 24 小時
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours} 小時前`
  }

  // 小於 7 天
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days} 天前`
  }

  // 超過 7 天,顯示完整日期
  return date.toLocaleDateString('zh-TW', {
    month: 'short',
    day: 'numeric',
  })
}

// 防抖搜尋
const handleSearchInput = useDebounceFn(async (value: string) => {
  const trimmed = value.trim()

  if (!trimmed) {
    searchResults.value = []
    isSearching.value = false
    return
  }

  // 關鍵字長度驗證
  if (trimmed.length < 2) {
    message.warning('搜尋關鍵字至少需要 2 個字元')
    return
  }

  isSearching.value = true
  try {
    const response = await searchSessions({
      keyword: trimmed,
      page: 1,
      page_size: SEARCH_PAGE_SIZE,
    })
    searchResults.value = response.items as ChatSession[]

    // 記錄到搜尋歷史
    addHistory(trimmed)
  }
  catch (error: any) {
    console.error('搜尋失敗:', error)
    if (error.response?.status === 429) {
      message.error('搜尋請求過於頻繁，請稍後再試')
    }
    else if (error.response?.status === 400) {
      message.error('搜尋關鍵字無效，請重新輸入')
    }
    else {
      message.error('搜尋失敗，請稍後再試')
    }
    searchResults.value = []
  }
  finally {
    isSearching.value = false
  }
}, SEARCH_DEBOUNCE_DELAY)

// 清空搜尋
function handleClearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

// 顯示的對話列表（搜尋結果 or 全部對話）
const displaySessions = computed(() => {
  return searchQuery.value.trim() ? searchResults.value : props.sessions
})

// 搜尋歷史選項（用於 NAutoComplete）
const historyOptions = computed(() =>
  history.value.map(item => ({
    label: item,
    value: item,
  })),
)

// 處理選擇 Session
function handleSelect(session: ChatSession) {
  emit('select', session)
}

// 處理建立新 Session
function handleCreate() {
  emit('create')
}

// 開啟重命名對話框
function openRenameModal(session: ChatSession, event: Event) {
  event.stopPropagation()
  renamingSession.value = session
  newTitle.value = session.title
  showRenameModal.value = true
}

// 確認重命名
function confirmRename() {
  if (!renamingSession.value) {
    return
  }

  const title = newTitle.value.trim()
  if (!title) {
    message.warning('標題不能為空')
    return
  }

  if (title === renamingSession.value.title) {
    showRenameModal.value = false
    return
  }

  emit('rename', renamingSession.value.id, title)
  showRenameModal.value = false
}

// 處理刪除
function handleDelete(session: ChatSession, event: Event) {
  event.stopPropagation()
  emit('delete', session.id)
}
</script>

<template>
  <div class="session-list-container">
    <!-- 頭部 -->
    <div class="list-header">
      <h3 class="header-title">
        對話列表
      </h3>
      <NButton
        type="primary"
        size="small"
        :disabled="loading"
        @click="handleCreate"
      >
        新建對話
      </NButton>
    </div>

    <!-- 搜尋欄 -->
    <div class="search-bar">
      <NAutoComplete
        v-model:value="searchQuery"
        :options="historyOptions"
        placeholder="搜尋對話標題或內容..."
        size="small"
        clearable
        :loading="isSearching"
        @update:value="handleSearchInput"
        @clear="handleClearSearch"
      >
        <template #prefix>
          <NIcon><SearchIcon /></NIcon>
        </template>
      </NAutoComplete>

      <!-- 搜尋結果計數 -->
      <div v-if="searchQuery.trim()" class="search-result-info">
        找到 {{ searchResults.length }} 個相關對話
        <NButton text size="tiny" @click="handleClearSearch">
          清除搜尋
        </NButton>
      </div>
    </div>

    <!-- 搜尋中提示 -->
    <div v-if="isSearching" class="searching-indicator">
      <NSpin size="small" />
      <span>搜尋中...</span>
    </div>

    <!-- 載入中 -->
    <div v-if="loading && sessions.length === 0" class="loading-container">
      <NSpin size="medium" />
    </div>

    <!-- Session 列表 -->
    <NList
      v-else-if="displaySessions.length > 0"
      hoverable
      clickable
      class="session-list"
      :class="{ 'searching-opacity': isSearching }"
    >
      <NListItem
        v-for="session in displaySessions"
        :key="session.id"
        class="session-item" :class="{ 'session-active': isCurrentSession(session.id) }"
        @click="handleSelect(session)"
      >
        <NThing>
          <template #header>
            <div class="session-header">
              <span class="session-title" v-html="highlightKeyword(session.title, searchQuery)" />
              <NTag
                :type="getGraphTypeColor(session.graph_type)"
                size="small"
                :bordered="false"
              >
                {{ getGraphTypeLabel(session.graph_type) }}
              </NTag>
            </div>
          </template>

          <template #description>
            <!-- 匹配的訊息片段（僅搜尋結果） -->
            <div
              v-if="isSessionSearchResult(session) && session.matched_snippets && session.matched_snippets.length > 0"
              class="matched-snippets"
            >
              <div
                v-for="(snippet, idx) in session.matched_snippets.slice(0, 2)"
                :key="idx"
                class="snippet"
                v-html="highlightKeyword(snippet, searchQuery)"
              />
              <div v-if="session.match_count && session.match_count > 2" class="more-matches">
                還有 {{ session.match_count - 2 }} 條相關訊息
              </div>
            </div>

            <!-- 時間和訊息數 -->
            <NSpace :size="8" align="center" :wrap="false">
              <NText :depth="3" style="font-size: 0.75rem">
                {{ formatTime(session.updated_at) }}
              </NText>
              <span v-if="session.message_count" class="message-count">
                {{ session.message_count }} 則訊息
              </span>
              <span v-if="isSessionSearchResult(session) && session.match_count" class="match-count">
                匹配 {{ session.match_count }} 條
              </span>
            </NSpace>
          </template>

          <template #footer>
            <NSpace :size="8">
              <NButton
                size="tiny"
                quaternary
                type="info"
                @click="(e: Event) => openRenameModal(session, e)"
              >
                重新命名
              </NButton>
              <NPopconfirm
                @positive-click="(e: Event) => handleDelete(session, e)"
              >
                <template #trigger>
                  <NButton
                    size="tiny"
                    quaternary
                    type="error"
                    @click.stop
                  >
                    刪除
                  </NButton>
                </template>
                確定要刪除這個對話嗎?
              </NPopconfirm>
            </NSpace>
          </template>
        </NThing>
      </NListItem>
    </NList>

    <!-- 空狀態 -->
    <div v-else class="empty-container">
      <NEmpty :description="searchQuery.trim() ? '沒有找到相關對話' : '尚無對話記錄'">
        <template #extra>
          <NButton v-if="searchQuery.trim()" type="primary" size="small" @click="handleClearSearch">
            查看全部對話
          </NButton>
          <NButton v-else type="primary" size="small" @click="handleCreate">
            建立第一個對話
          </NButton>
        </template>
      </NEmpty>
    </div>

    <!-- 重命名對話框 -->
    <NModal
      v-model:show="showRenameModal"
      preset="dialog"
      title="重命名對話"
      positive-text="確認"
      negative-text="取消"
      @positive-click="confirmRename"
    >
      <div style="padding: 12px 0">
        <NInput
          v-model:value="newTitle"
          placeholder="請輸入新的標題"
          :maxlength="100"
          show-count
          clearable
          @keydown.enter="confirmRename"
        />
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.session-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
  overflow: hidden;
}

/* 頭部 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
  backdrop-filter: blur(8px);
}

.header-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

/* 搜尋欄 */
.search-bar {
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
}

.search-result-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.75rem;
  color: #6b7280;
}

.searching-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: #eff6ff;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
  color: #3b82f6;
}

/* 載入中 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 200px;
}

/* Session 列表 */
.session-list {
  flex: 1;
  overflow-y: auto;
}

.session-list.searching-opacity {
  opacity: 0.6;
}

.session-item {
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.session-item:hover {
  background: linear-gradient(135deg, #f9fafb 0%, #f5f3ff 100%);
}

.session-active {
  background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
  border-left-color: #8b5cf6;
}

.session-active:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #ede9fe 100%);
}

/* Session 頭部 */
.session-header {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.session-title {
  font-weight: 500;
  font-size: 0.9375rem;
  color: #1f2937;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 高亮樣式 */
.session-title :deep(.search-highlight) {
  background-color: #fef08a;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

/* 匹配片段 */
.matched-snippets {
  margin-top: 6px;
  margin-bottom: 8px;
  padding: 8px;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 0.8125rem;
  color: #4b5563;
}

.snippet {
  margin-bottom: 4px;
  line-height: 1.4;
}

.snippet:last-of-type {
  margin-bottom: 0;
}

.snippet :deep(.search-highlight) {
  background-color: #fef08a;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

.more-matches {
  margin-top: 6px;
  font-size: 0.75rem;
  color: #9ca3af;
  font-style: italic;
}

.message-count {
  font-size: 0.75rem;
  color: #9ca3af;
}

.match-count {
  font-size: 0.75rem;
  color: #3b82f6;
  font-weight: 500;
}

/* 空狀態 */
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 200px;
}

/* 滾動條樣式 */
.session-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-track {
  background: transparent;
}

.session-list::-webkit-scrollbar-thumb {
  background: rgba(203, 213, 225, 0.6);
  border-radius: 3px;
  transition: background 0.2s ease;
}

.session-list::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.8);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .list-header {
    padding: 12px 16px;
  }

  .header-title {
    font-size: 1rem;
  }

  .search-bar {
    padding: 10px 16px;
  }
}
</style>
