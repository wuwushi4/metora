<script setup lang="ts">
import type { PromptTemplate } from '@/types/prompt'
import {
  AddOutline as AddIcon,
  CheckmarkCircleOutline as CheckIcon,
  TrashOutline as DeleteIcon,
  CreateOutline as EditIcon,
  Star as StarFilledIcon,
  StarOutline as StarIcon,
} from '@vicons/ionicons5'
import {
  NButton,
  NCard,
  NEmpty,
  NIcon,
  NPopconfirm,
  NScrollbar,
  NSpin,
  NTag,
  NTooltip,
} from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { usePromptsStore } from '@/stores/prompts'
import PromptTemplateEditor from './PromptTemplateEditor.vue'

const promptsStore = usePromptsStore()
const chatStore = useChatStore()

// 編輯器狀態
const showEditor = ref(false)
const editingTemplate = ref<PromptTemplate | null>(null)

// 載入狀態
const templates = computed(() => promptsStore.activeTemplates)
const loading = computed(() => promptsStore.isLoading)
const selectedPromptId = computed(() => chatStore.selectedPromptTemplateId)

// 初始化
onMounted(async () => {
  await promptsStore.loadTemplates()
})

// 開啟建立對話框
function handleCreate() {
  editingTemplate.value = null
  showEditor.value = true
}

// 開啟編輯對話框
function handleEdit(template: PromptTemplate) {
  editingTemplate.value = template
  showEditor.value = true
}

// 確認建立/更新
async function handleConfirm(data: any) {
  try {
    if (editingTemplate.value) {
      // 更新
      await promptsStore.updateTemplate(editingTemplate.value.id, data)
    }
    else {
      // 建立
      await promptsStore.createTemplate(data)
    }
    showEditor.value = false
  }
  catch (error) {
    console.error('操作失敗:', error)
  }
}

// 刪除模板
async function handleDelete(template: PromptTemplate) {
  try {
    // 如果刪除的是當前選擇的模板，清除選擇
    if (selectedPromptId.value === template.id) {
      chatStore.clearPromptTemplate()
    }
    await promptsStore.deleteTemplate(template.id)
  }
  catch (error) {
    console.error('刪除失敗:', error)
  }
}

// 切換收藏狀態
async function handleToggleFavorite(template: PromptTemplate) {
  try {
    await promptsStore.toggleFavorite(template.id)
  }
  catch (error) {
    console.error('切換收藏狀態失敗:', error)
  }
}

// 選擇提示詞模板
function handleSelect(template: PromptTemplate) {
  if (selectedPromptId.value === template.id) {
    // 如果已選擇，則取消選擇
    chatStore.clearPromptTemplate()
  }
  else {
    // 選擇此模板
    chatStore.selectPromptTemplate(template.id)
  }
}

// 判斷是否選中
function isSelected(templateId: string): boolean {
  return selectedPromptId.value === templateId
}
</script>

<template>
  <div class="prompt-panel">
    <!-- 頂部標題和操作按鈕 -->
    <div class="panel-header">
      <div class="header-title">
        <span class="title-icon">💡</span>
        <span class="title-text">提示詞模板</span>
      </div>
      <NButton
        size="small"
        type="primary"
        :disabled="loading"
        @click="handleCreate"
      >
        <template #icon>
          <NIcon><AddIcon /></NIcon>
        </template>
        新增
      </NButton>
    </div>

    <!-- 提示詞列表 -->
    <div class="panel-content">
      <NSpin :show="loading">
        <NScrollbar v-if="templates.length > 0" class="template-scrollbar">
          <div class="template-list">
            <NCard
              v-for="template in templates"
              :key="template.id"
              class="template-card" :class="[
                { selected: isSelected(template.id) },
              ]"
              size="small"
              hoverable
              @click="handleSelect(template)"
            >
              <!-- 卡片頂部 -->
              <div class="card-header">
                <div class="card-title">
                  <span class="template-name">{{ template.name }}</span>
                  <NTag
                    v-if="template.is_favorite"
                    size="small"
                    type="warning"
                    :bordered="false"
                    class="default-tag"
                  >
                    收藏
                  </NTag>
                </div>
                <div class="card-actions" @click.stop>
                  <!-- 收藏按鈕 -->
                  <NTooltip>
                    <template #trigger>
                      <NButton
                        size="tiny"
                        quaternary
                        circle
                        @click="handleToggleFavorite(template)"
                      >
                        <template #icon>
                          <NIcon>
                            <StarFilledIcon v-if="template.is_favorite" class="text-yellow-500" />
                            <StarIcon v-else />
                          </NIcon>
                        </template>
                      </NButton>
                    </template>
                    {{ template.is_favorite ? '取消收藏' : '收藏' }}
                  </NTooltip>

                  <!-- 編輯按鈕 -->
                  <NTooltip>
                    <template #trigger>
                      <NButton
                        size="tiny"
                        quaternary
                        circle
                        @click="handleEdit(template)"
                      >
                        <template #icon>
                          <NIcon><EditIcon /></NIcon>
                        </template>
                      </NButton>
                    </template>
                    編輯
                  </NTooltip>

                  <!-- 刪除按鈕 -->
                  <NPopconfirm
                    positive-text="確認"
                    negative-text="取消"
                    @positive-click="handleDelete(template)"
                  >
                    <template #trigger>
                      <NTooltip>
                        <template #trigger>
                          <NButton
                            size="tiny"
                            quaternary
                            circle
                          >
                            <template #icon>
                              <NIcon><DeleteIcon /></NIcon>
                            </template>
                          </NButton>
                        </template>
                        刪除
                      </NTooltip>
                    </template>
                    確定要刪除此提示詞模板嗎？
                  </NPopconfirm>
                </div>
              </div>

              <!-- 描述 -->
              <div v-if="template.description" class="card-description">
                {{ template.description }}
              </div>

              <!-- 內容預覽 -->
              <div class="card-content">
                {{ template.content.length > 100 ? `${template.content.substring(0, 100)}...` : template.content }}
              </div>

              <!-- 選中標記 -->
              <div v-if="isSelected(template.id)" class="selected-badge">
                <NIcon size="18" color="#0ea5e9">
                  <CheckIcon />
                </NIcon>
              </div>
            </NCard>
          </div>
        </NScrollbar>

        <!-- 空狀態 -->
        <div v-else class="empty-state">
          <NEmpty
            description="尚未建立提示詞模板"
            size="large"
          >
            <template #extra>
              <NButton
                type="primary"
                @click="handleCreate"
              >
                <template #icon>
                  <NIcon><AddIcon /></NIcon>
                </template>
                建立第一個模板
              </NButton>
            </template>
          </NEmpty>
        </div>
      </NSpin>
    </div>

    <!-- 編輯器 Modal -->
    <PromptTemplateEditor
      v-model:show="showEditor"
      :template="editingTemplate"
      :loading="promptsStore.loadingStates.creating || promptsStore.loadingStates.updating"
      @confirm="handleConfirm"
    />
  </div>
</template>

<style scoped>
.prompt-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.8) 0%, rgba(243, 232, 255, 0.8) 100%);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.panel-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.template-scrollbar {
  height: 100%;
  padding: 12px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-card {
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.template-card:hover {
  border-color: #e0e7ff;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
}

.template-card.selected {
  border-color: #0ea5e9;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(255, 255, 255, 0.95) 100%);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.25);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.card-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.template-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.default-tag {
  font-size: 11px;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.card-description {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.5;
}

.card-content {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background: rgba(249, 250, 251, 0.8);
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.selected-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}
</style>
