<script setup lang="ts">
import type { RegulationDetail } from '@/types/regulation'
import {
  ArrowBackOutline as BackIcon,
  DocumentTextOutline as DocumentIcon,
  DownloadOutline as DownloadIcon,
  CreateOutline as EditIcon,
  RefreshOutline as RefreshIcon,
} from '@vicons/ionicons5'
import {
  NButton,
  NCard,
  NCollapse,
  NCollapseItem,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NEmpty,
  NIcon,
  NInput,
  NSpace,
  NSpin,
  NTag,
} from 'naive-ui'
import { useBreakpoints } from '@vueuse/core'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { exportRegulation, getRegulationById, updateRegulation } from '@/api/regulations'
import { message } from '@/utils/message'

const route = useRoute()
const router = useRouter()

// 狀態
const loading = ref(false)
const regulation = ref<RegulationDetail | null>(null)

// 編輯模式狀態
const isEditing = ref(false)
const editingRegulation = ref<RegulationDetail | null>(null)
const saving = ref(false)

// 每個 article 的新增情境輸入框
const newScenarioInputs = ref<Record<string, string>>({})

const breakpoints = useBreakpoints({ mobile: 768 })
const descriptionColumn = computed(() => breakpoints.smaller('mobile').value ? 1 : 2)

// Regulation ID
const regulationId = computed(() => {
  return Number(route.params.id)
})

// 法規狀態映射
const statusMap: Record<string, { label: string, type: 'success' | 'warning' | 'error' | 'info' }> = {
  現行: { label: '現行', type: 'success' },
  廢止: { label: '廢止', type: 'error' },
  停止適用: { label: '停止適用', type: 'warning' },
  尚未生效: { label: '尚未生效', type: 'info' },
}

// 遞歸格式化 item 及其 subitems
function formatItem(item: any, level: number = 0): string {
  const indent = '  '.repeat(level)
  const display = item.item_display || item.subitem_display || ''
  let result = `${indent}${display}、${item.content}`

  // 遞歸處理 subitems
  if (item.subitems && Array.isArray(item.subitems) && item.subitems.length > 0) {
    const subitemTexts = item.subitems.map((subitem: any) =>
      formatItem(subitem, level + 1),
    )
    result += `\n${subitemTexts.join('\n')}`
  }

  return result
}

// 格式化條文內容（動態處理 items/subitems）
function formatArticleContent(article: any): string {
  // 如果有 items，動態格式化
  if (article.items && Array.isArray(article.items) && article.items.length > 0) {
    const itemTexts = article.items.map((item: any) => formatItem(item, 0))

    // 如果有引導文字，保留並追加
    if (article.content && article.content.trim() !== '') {
      return `${article.content}\n\n${itemTexts.join('\n\n')}`
    }
    else {
      return itemTexts.join('\n\n')
    }
  }

  // 沒有 items，直接返回 content
  return article.content || ''
}

// 載入法規資訊
async function loadRegulation() {
  loading.value = true
  try {
    regulation.value = await getRegulationById(regulationId.value)
  }
  catch (error: any) {
    console.error('載入法規失敗:', error)
    message.error(error.message || '載入法規失敗')
    // 載入失敗返回列表頁
    router.push('/regulations')
  }
  finally {
    loading.value = false
  }
}

// 返回列表頁
function handleBack() {
  router.push('/regulations')
}

// 手動重新整理
async function handleRefresh() {
  await loadRegulation()
  message.success('重新整理成功')
}

// 進入編輯模式
function handleEdit() {
  if (!regulation.value)
    return
  // 深拷貝避免直接修改原始資料
  editingRegulation.value = JSON.parse(JSON.stringify(regulation.value))
  isEditing.value = true
}

// 獲取輸入框的 key
function getScenarioInputKey(chapterIndex: number, articleIndex: number): string {
  return `${chapterIndex}-${articleIndex}`
}

// 新增情境
function handleAddScenario(chapterIndex: number, articleIndex: number) {
  const key = getScenarioInputKey(chapterIndex, articleIndex)
  const value = newScenarioInputs.value[key]?.trim()

  if (!value)
    return

  const article = getEditingArticle(chapterIndex, articleIndex)
  if (!article.scenarios) {
    article.scenarios = []
  }
  article.scenarios.push(value)
  newScenarioInputs.value[key] = ''
}

// 刪除情境
function handleRemoveScenario(chapterIndex: number, articleIndex: number, scenarioIndex: number) {
  const article = getEditingArticle(chapterIndex, articleIndex)
  article.scenarios?.splice(scenarioIndex, 1)
}

// 取消編輯
function handleCancelEdit() {
  editingRegulation.value = null
  isEditing.value = false
  newScenarioInputs.value = {} // 清空輸入框
}

// 保存編輯
async function handleSave() {
  if (!editingRegulation.value)
    return

  saving.value = true
  try {
    await updateRegulation(editingRegulation.value.id, {
      content: editingRegulation.value.content,
    })

    message.success('法規更新成功')
    isEditing.value = false
    editingRegulation.value = null
    // 重新載入資料
    await loadRegulation()
  }
  catch (error: any) {
    console.error('更新法規失敗:', error)
    message.error(error.message || '更新法規失敗')
  }
  finally {
    saving.value = false
  }
}

// 獲取編輯中的 article（用於雙向綁定）
function getEditingArticle(chapterIndex: number, articleIndex: number): { scenarios: string[] } {
  if (!editingRegulation.value)
    return { scenarios: [] }
  const chapter = editingRegulation.value.content.chapters?.[chapterIndex]
  if (!chapter)
    return { scenarios: [] }
  const article = chapter.articles?.[articleIndex]
  if (!article)
    return { scenarios: [] }
  return article
}

// 處理導出法規
async function handleExport() {
  if (!regulation.value)
    return

  const loadingMessage = message.loading('正在導出法規...', { duration: 0 })

  try {
    const blob = await exportRegulation(regulation.value.id)

    // 建立下載連結
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${regulation.value.law_name}_${regulation.value.law_code}.json`

    // 觸發下載
    document.body.appendChild(link)
    link.click()

    // 清理
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    loadingMessage.destroy()
    message.success('法規導出成功')
  }
  catch (error: any) {
    loadingMessage.destroy()
    console.error('導出法規失敗:', error)
    message.error(error.message || '導出法規失敗')
  }
}

// 頁面載入時獲取資料
onMounted(async () => {
  await loadRegulation()
})
</script>

<template>
  <div class="regulation-detail-wrapper">
    <!-- 頁面標題（固定在頂部） -->
    <div class="page-header">
      <div class="header-left">
        <NButton @click="handleBack">
          <template #icon>
            <NIcon :component="BackIcon" />
          </template>
          返回列表
        </NButton>
        <div class="header-content">
          <h1 class="page-title">
            {{ regulation?.law_name || 'Loading...' }}
          </h1>
          <p class="page-description">
            法規詳細資訊與章節條文
          </p>
        </div>
      </div>
      <div class="header-actions">
        <template v-if="!isEditing">
          <NButton @click="handleRefresh">
            <template #icon>
              <NIcon>
                <RefreshIcon />
              </NIcon>
            </template>
            重新整理
          </NButton>
          <NButton @click="handleExport">
            <template #icon>
              <NIcon>
                <DownloadIcon />
              </NIcon>
            </template>
            導出
          </NButton>
          <NButton type="primary" @click="handleEdit">
            <template #icon>
              <NIcon>
                <EditIcon />
              </NIcon>
            </template>
            編輯情境
          </NButton>
        </template>
        <template v-else>
          <NButton @click="handleCancelEdit">
            取消
          </NButton>
          <NButton type="primary" :loading="saving" @click="handleSave">
            保存
          </NButton>
        </template>
      </div>
    </div>

    <!-- 可滾動的內容區域 -->
    <div class="regulation-content-scroll">
      <NSpin :show="loading">
        <NCard v-if="regulation" title="法規基本資訊" class="info-card">
          <NDescriptions :column="descriptionColumn" label-placement="left">
            <NDescriptionsItem label="ID">
              {{ regulation.id }}
            </NDescriptionsItem>
            <NDescriptionsItem label="法規代碼">
              {{ regulation.law_code }}
            </NDescriptionsItem>
            <NDescriptionsItem label="法規名稱">
              {{ regulation.law_name }}
            </NDescriptionsItem>
            <NDescriptionsItem label="法規類別">
              {{ regulation.category }}
            </NDescriptionsItem>
            <NDescriptionsItem label="法規狀態">
              <NTag
                :type="statusMap[regulation.status]?.type || 'info'"
                size="small"
              >
                {{ statusMap[regulation.status]?.label || regulation.status }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="最後更新">
              {{ regulation.last_updated || '-' }}
            </NDescriptionsItem>
            <NDescriptionsItem label="章節總數">
              {{ regulation.total_chapters }}
            </NDescriptionsItem>
            <NDescriptionsItem label="條文總數">
              {{ regulation.total_articles }}
            </NDescriptionsItem>
            <NDescriptionsItem label="情境總數">
              {{ regulation.total_scenarios }}
            </NDescriptionsItem>
            <NDescriptionsItem label="所有者">
              {{ regulation.owner?.full_name || regulation.owner?.username || `使用者 #${regulation.user_id}` }}
            </NDescriptionsItem>
            <NDescriptionsItem label="建立時間">
              {{ new Date(regulation.created_at).toLocaleString('zh-TW') }}
            </NDescriptionsItem>
            <NDescriptionsItem label="更新時間">
              {{ new Date(regulation.updated_at).toLocaleString('zh-TW') }}
            </NDescriptionsItem>
          </NDescriptions>
        </NCard>

        <!-- 章節與條文內容 -->
        <NCard v-if="regulation && regulation.content" title="章節與條文" class="content-card">
          <NCollapse v-if="regulation.content.chapters && regulation.content.chapters.length > 0">
            <NCollapseItem
              v-for="(chapter, chapterIndex) in regulation.content.chapters"
              :key="chapterIndex"
              :name="`chapter-${chapterIndex}`"
            >
              <template #header>
                <div class="chapter-header">
                  <span class="chapter-display">{{ chapter.chapter_display }}</span>
                  <span class="chapter-name">{{ chapter.chapter_name }}</span>
                  <NTag size="small" :bordered="false">
                    {{ chapter.articles?.length || 0 }} 條
                  </NTag>
                </div>
              </template>

              <!-- 條文列表 -->
              <div v-if="chapter.articles && chapter.articles.length > 0" class="articles-container">
                <div
                  v-for="(article, articleIndex) in chapter.articles"
                  :key="articleIndex"
                  class="article-item"
                >
                  <div class="article-header">
                    <NIcon :component="DocumentIcon" class="article-icon" />
                    <span class="article-display">{{ article.article_display }}</span>
                  </div>

                  <div class="article-content">
                    {{ formatArticleContent(article) }}
                  </div>

                  <NDivider />

                  <!-- 檢視模式 -->
                  <template v-if="!isEditing">
                    <div v-if="article.scenarios && article.scenarios.length > 0" class="scenarios-section">
                      <div class="scenarios-label">
                        應用情境：
                      </div>
                      <NSpace vertical :size="8">
                        <NTag
                          v-for="(scenario, scenarioIndex) in article.scenarios"
                          :key="scenarioIndex"
                          type="info"
                          size="small"
                          class="scenario-tag-display"
                        >
                          {{ scenario }}
                        </NTag>
                      </NSpace>
                    </div>

                    <div v-else class="scenarios-section">
                      <div class="scenarios-label">
                        應用情境：
                      </div>
                      <NTag type="default" size="small">
                        無
                      </NTag>
                    </div>
                  </template>

                  <!-- 編輯模式 -->
                  <template v-else>
                    <div class="scenarios-section">
                      <div class="scenarios-label">
                        應用情境：
                      </div>
                      <div class="custom-scenarios-editor">
                        <!-- 現有標籤列表（垂直排列） -->
                        <NSpace
                          v-if="getEditingArticle(chapterIndex, articleIndex).scenarios?.length"
                          vertical
                          :size="8"
                        >
                          <NTag
                            v-for="(scenario, scenarioIndex) in getEditingArticle(chapterIndex, articleIndex).scenarios"
                            :key="scenarioIndex"
                            closable
                            size="small"
                            type="info"
                            class="scenario-tag-edit"
                            @close="handleRemoveScenario(chapterIndex, articleIndex, scenarioIndex)"
                          >
                            {{ scenario }}
                          </NTag>
                        </NSpace>

                        <!-- 新增輸入框 -->
                        <NInput
                          v-model:value="newScenarioInputs[getScenarioInputKey(chapterIndex, articleIndex)]"
                          type="textarea"
                          placeholder="輸入情境描述（支援多行），點擊「新增情境」按鈕加入"
                          size="small"
                          :autosize="{
                            minRows: 2,
                            maxRows: 6,
                          }"
                        />
                        <NButton
                          size="small"
                          type="primary"
                          :disabled="!newScenarioInputs[getScenarioInputKey(chapterIndex, articleIndex)]?.trim()"
                          style="align-self: flex-start;"
                          @click="handleAddScenario(chapterIndex, articleIndex)"
                        >
                          新增情境
                        </NButton>
                      </div>
                    </div>
                  </template>
                </div>
              </div>

              <NEmpty v-else description="此章節無條文" />
            </NCollapseItem>
          </NCollapse>

          <NEmpty v-else description="此法規無章節內容" />
        </NCard>
      </NSpin>
    </div>
  </div>
</template>

<style scoped>
.regulation-detail-wrapper {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
  background-color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  border-bottom: 2px solid #e5e7eb;
  z-index: 10;
}

.regulation-content-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
}

/* 優化滾動條樣式 */
.regulation-content-scroll::-webkit-scrollbar {
  width: 8px;
}

.regulation-content-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.regulation-content-scroll::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.regulation-content-scroll::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.page-description {
  margin: 8px 0 0;
  font-size: 0.9375rem;
  color: #6b7280;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.info-card {
  margin-bottom: 24px;
}

.content-card {
  margin-bottom: 24px;
}

/* 章節標題 */
.chapter-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.chapter-display {
  font-weight: 600;
  color: #111827;
}

.chapter-name {
  color: #6b7280;
}

/* 條文容器 */
.articles-container {
  padding: 16px 0;
}

.article-item {
  padding: 16px;
  margin-bottom: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.article-item:last-child {
  margin-bottom: 0;
}

.article-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.article-icon {
  font-size: 18px;
  color: #0ea5e9;
}

.article-display {
  font-weight: 600;
  font-size: 1rem;
  color: #111827;
}

.article-content {
  padding: 12px 0;
  line-height: 1.8;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 情境區塊 */
.scenarios-section {
  margin-top: 12px;
}

.scenarios-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 8px;
}

/* 自訂情境編輯器 */
.custom-scenarios-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

/* 查看模式和編輯模式的標籤樣式 */
.scenario-tag-display,
.scenario-tag-edit {
  max-width: 100%;
  white-space: pre-wrap;
  word-break: break-all;
  text-align: left;
  display: inline-flex;
  width: fit-content;
  padding: 8px 12px !important;
  line-height: 1.6 !important;
  height: auto !important;
  min-height: auto !important;
}

/* 編輯模式特定樣式 */
.scenario-tag-edit {
  cursor: pointer;
}

/* NSpace 容器寬度 */
.scenarios-section .n-space {
  width: 100%;
}

/* 確保標籤內的文字換行正確 */
.scenario-tag-display :deep(.n-tag__content),
.scenario-tag-edit :deep(.n-tag__content) {
  white-space: pre-wrap;
  word-break: break-all;
  max-width: 100%;
}

@media (max-width: 768px) {
  .regulation-detail-wrapper {
    height: calc(100vh - 56px);
  }

  .regulation-content-scroll {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .header-left {
    width: 100%;
    flex-direction: column;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions button {
    flex: 1;
  }
}
</style>
