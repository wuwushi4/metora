<script setup lang="ts">
import type { GraphInfo } from '@/types/chat'
import { NCard, NSpace, NSpin, NText } from 'naive-ui'
import { computed } from 'vue'

interface Props {
  modelValue: 'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph' | null
  graphs: GraphInfo[]
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: 'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph']
}>()

// 雙向綁定值
const selectedGraph = computed({
  get: () => props.modelValue,
  set: (value) => {
    if (value) {
      emit('update:modelValue', value)
    }
  },
})

// 查找 Graph 資訊
function getGraphInfo(graphType: string): GraphInfo | undefined {
  return props.graphs.find(g => g.graph_type === graphType)
}

// Agent 選項資訊（只顯示後端已註冊的 Graph）
const allGraphOptions = [
    {
      value: 'base_graph' as const,
      label: '通用助理',
      description: '我可以協助您處理各種日常問題,基於豐富的通用知識為您提供解答',
      icon: '🤖',
      role: '通用對話專家',
      info: getGraphInfo('base_graph'),
    },
    {
      value: 'rag_graph' as const,
      label: '知識專家',
      description: '我專精於您的知識庫內容,能夠精準檢索並回答基於文檔的專業問題',
      icon: '🎓',
      role: '知識檢索專家',
      info: getGraphInfo('rag_graph'),
    },
    {
      value: 'regulation_graph' as const,
      label: '法規顧問',
      description: '我專注於法規分析與解讀,能夠協助您查詢條文、追蹤引用關係並提供專業建議',
      icon: '⚖️',
      role: '法規查詢專家',
      info: getGraphInfo('regulation_graph'),
    },
    {
      value: 'agent_graph' as const,
      label: '工具 Agent',
      description: '我可以撰寫並執行 Python 程式碼來解決複雜問題,包括資料分析、圖表生成和 API 呼叫',
      icon: '🛠️',
      role: '程式碼執行專家',
      info: getGraphInfo('agent_graph'),
    },
  ]

const graphOptions = computed(() => {
  // 根據後端返回的 graphs 列表過濾選項
  if (props.graphs.length === 0) {
    return allGraphOptions
  }
  const availableTypes = new Set(props.graphs.map(g => g.graph_type))
  return allGraphOptions.filter(opt => availableTypes.has(opt.value))
})
</script>

<template>
  <div class="graph-selector">
    <div class="selector-header">
      <NText :depth="3" style="font-size: 0.875rem">
        選擇要聊天的 AI 助理，不同的助理擁有各自的專長領域
      </NText>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="loading-container">
      <NSpin size="small" />
      <NText :depth="3">
        載入中...
      </NText>
    </div>

    <!-- Graph 選項卡片 -->
    <div v-else class="graph-options">
      <NCard
        v-for="option in graphOptions"
        :key="option.value"
        class="graph-option-card" :class="[
          { 'graph-option-selected': selectedGraph === option.value },
          { 'graph-option-disabled': disabled },
        ]"
        :bordered="true"
        hoverable
        @click="!disabled && (selectedGraph = option.value)"
      >
        <div class="graph-option-content">
          <!-- 圖示 -->
          <div class="graph-icon">
            {{ option.icon }}
          </div>

          <!-- 資訊 -->
          <div class="graph-info">
            <div class="graph-label">
              <span class="label-text">{{ option.label }}</span>
              <div
                v-if="selectedGraph === option.value"
                class="selected-indicator"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
            </div>
            <NText :depth="2" class="graph-description">
              {{ option.description }}
            </NText>

            <!-- Graph 詳細資訊 -->
            <div v-if="option.info" class="graph-details">
              <NSpace :size="6" align="center">
                <NText :depth="3" style="font-size: 0.75rem">
                  {{ option.info.name }}
                </NText>
                <span v-if="option.info.description" class="detail-separator">•</span>
                <NText :depth="3" style="font-size: 0.75rem">
                  {{ option.info.description }}
                </NText>
              </NSpace>
            </div>
          </div>
        </div>
      </NCard>
    </div>

    <!-- 提示 -->
    <div v-if="!loading" class="selector-hint">
      <NText :depth="3" style="font-size: 0.8125rem">
        💡 提示: 知識專家和法規顧問需要先選擇知識庫；工具 Agent 可執行程式碼解決複雜問題
      </NText>
    </div>
  </div>
</template>

<style scoped>
.graph-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 頭部 */
.selector-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;
}

.selector-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

/* 載入中 */
.loading-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  justify-content: center;
}

/* Graph 選項 - Grid 佈局 */
.graph-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.graph-option-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid #e5e7eb;
  min-height: 220px;
  display: flex;
  flex-direction: column;
}

.graph-option-card:hover:not(.graph-option-disabled) {
  border-color: #3b82f6;
  box-shadow:
    0 8px 12px -2px rgba(59, 130, 246, 0.15),
    0 4px 6px -1px rgba(59, 130, 246, 0.1);
  transform: translateY(-4px);
}

.graph-option-selected {
  border-color: #3b82f6;
  background: linear-gradient(to bottom, #eff6ff, #ffffff);
  box-shadow:
    0 4px 6px -1px rgba(59, 130, 246, 0.2),
    0 2px 4px -1px rgba(59, 130, 246, 0.1);
}

.graph-option-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.graph-option-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  text-align: center;
  padding: 4px;
}

/* 圖示 - Agent 頭像風格 */
.graph-icon {
  font-size: 2.25rem;
  width: 65px;
  height: 65px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.graph-option-card:hover:not(.graph-option-disabled) .graph-icon {
  transform: scale(1.05);
}

/* 資訊 */
.graph-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.graph-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
}

.label-text {
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1f2937;
}

.selected-indicator {
  color: #3b82f6;
  display: flex;
  align-items: center;
  position: absolute;
  top: -32px;
  right: -16px;
}

.graph-description {
  font-size: 0.8125rem;
  line-height: 1.6;
  color: #6b7280;
}

.graph-details {
  padding-top: 4px;
}

.detail-separator {
  color: #d1d5db;
  font-size: 0.75rem;
}

/* 提示 */
.selector-hint {
  padding: 10px 14px;
  background: #fef3c7;
  border-radius: 8px;
  border-left: 3px solid #f59e0b;
}

/* 深色模式支援 */
@media (prefers-color-scheme: dark) {
  .selector-title {
    color: #f9fafb;
  }

  .graph-option-card {
    background: #1f2937;
    border-color: #374151;
  }

  .graph-option-card:hover:not(.graph-option-disabled) {
    border-color: #3b82f6;
  }

  .graph-option-selected {
    background: linear-gradient(to bottom, #1e3a5f, #1f2937);
  }

  .graph-icon {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  }

  .label-text {
    color: #f9fafb;
  }

  .graph-description {
    color: #9ca3af;
  }

  .selector-hint {
    background: #422006;
    border-left-color: #f59e0b;
  }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .graph-options {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .graph-option-card {
    min-height: 220px;
  }

  .graph-icon {
    width: 60px;
    height: 60px;
    font-size: 2.25rem;
  }

  .label-text {
    font-size: 1rem;
  }

  .graph-description {
    font-size: 0.8125rem;
  }

  .selected-indicator {
    top: -28px;
    right: -12px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .graph-options {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1025px) {
  .graph-options {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }
}
</style>
