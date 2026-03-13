<script setup lang="ts">
import { NCard, NSpace, NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { tm } = useI18n()

interface Props {
  graphType?: 'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph' | null
}

const props = withDefaults(defineProps<Props>(), {
  graphType: null,
})

// 發出點擊示例的事件
const emit = defineEmits<{
  selectExample: [question: string]
}>()

// 示例問題 key 映射
const exampleKeyMap: Record<string, string> = {
  base_graph: 'chat.empty.baseExamples',
  rag_graph: 'chat.empty.ragExamples',
  regulation_graph: 'chat.empty.regulationExamples',
  agent_graph: 'chat.empty.agentExamples',
}

// 獲取當前模式的示例問題
function getExamples(): string[] {
  if (!props.graphType) {
    return []
  }
  const key = exampleKeyMap[props.graphType]
  if (!key) return []
  const examples = tm(key)
  return Array.isArray(examples) ? examples : []
}

function handleExampleClick(question: string) {
  emit('selectExample', question)
}
</script>

<template>
  <div class="empty-chat-container">
    <!-- 空狀態圖示 -->
    <div class="empty-icon">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="80"
        height="80"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    </div>

    <!-- 歡迎文字 -->
    <div class="welcome-text">
      <h2 class="welcome-title">
        {{ $t('chat.empty.title') }}
      </h2>
      <p class="welcome-description">
        <template v-if="graphType === 'rag_graph'">
          {{ $t('chat.empty.descRag') }}
        </template>
        <template v-else-if="graphType === 'base_graph'">
          {{ $t('chat.empty.descBase') }}
        </template>
        <template v-else-if="graphType === 'regulation_graph'">
          {{ $t('chat.empty.descRegulation') }}
        </template>
        <template v-else-if="graphType === 'agent_graph'">
          {{ $t('chat.empty.descAgent') }}
        </template>
        <template v-else>
          {{ $t('chat.empty.descDefault') }}
        </template>
      </p>
    </div>

    <!-- 示例問題 -->
    <div v-if="getExamples().length > 0" class="examples-section">
      <NText class="examples-title" :depth="3">
        {{ $t('chat.empty.examplesTitle') }}
      </NText>
      <NSpace vertical :size="12">
        <NCard
          v-for="(question, index) in getExamples()"
          :key="index"
          :bordered="true"
          hoverable
          size="small"
          class="example-card"
          @click="handleExampleClick(question)"
        >
          <div class="example-content">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="example-icon"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span class="example-text">{{ question }}</span>
          </div>
        </NCard>
      </NSpace>
    </div>

    <!-- 提示區塊 -->
    <div class="tips-section">
      <div class="tip-item">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="tip-icon"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <NText :depth="3" class="tip-text">
          {{ $t('chat.empty.tip') }}
        </NText>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-chat-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  padding: 40px 20px;
  gap: 32px;
}

/* 空狀態圖示 */
.empty-icon {
  color: #cbd5e1;
}

/* 歡迎文字 */
.welcome-text {
  text-align: center;
  max-width: 500px;
}

.welcome-title {
  margin: 0 0 12px 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
}

.welcome-description {
  margin: 0;
  font-size: 1rem;
  line-height: 1.6;
  color: #6b7280;
}

/* 示例問題區 */
.examples-section {
  width: 100%;
  max-width: 600px;
}

.examples-title {
  display: block;
  margin-bottom: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  text-align: center;
}

.example-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border-color: #e5e7eb;
}

.example-card:hover {
  border-color: #8b5cf6;
  box-shadow:
    0 4px 12px rgba(139, 92, 246, 0.2),
    0 2px 6px rgba(14, 165, 233, 0.1);
  transform: translateY(-2px);
}

.example-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.example-icon {
  flex-shrink: 0;
  color: #8b5cf6;
}

.example-text {
  font-size: 0.9375rem;
  color: #374151;
  line-height: 1.5;
}

/* 提示區塊 */
.tips-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 600px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%);
  border-radius: 8px;
  border-left: 3px solid #8b5cf6;
}

.tip-icon {
  flex-shrink: 0;
  background: linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tip-text {
  font-size: 0.875rem;
  line-height: 1.5;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .empty-chat-container {
    padding: 24px 16px;
    gap: 24px;
    min-height: 300px;
  }

  .welcome-title {
    font-size: 1.5rem;
  }

  .welcome-description {
    font-size: 0.9375rem;
  }

  .empty-icon svg {
    width: 60px;
    height: 60px;
  }
}
</style>
