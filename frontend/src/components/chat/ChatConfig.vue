<script setup lang="ts">
import type { CSSProperties } from 'vue'
import type { GraphInfo, SessionCreateRequest } from '@/types/chat'
import { useWindowSize } from '@vueuse/core'
import { NButton, NDivider, NInput, NModal, NSpace, NText } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { message } from '@/utils/message'
import { useI18n } from 'vue-i18n'
import CollectionSelector from './CollectionSelector.vue'
import GraphSelector from './GraphSelector.vue'

const { t } = useI18n()

interface Props {
  show: boolean
  graphs: GraphInfo[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'confirm': [config: SessionCreateRequest]
}>()

// 響應式視窗尺寸
const { width } = useWindowSize()

// 配置狀態
const selectedGraph = ref<'base_graph' | 'rag_graph' | 'regulation_graph' | 'agent_graph' | null>(null)
const selectedCollections = ref<number[]>([])
const sessionTitle = ref('')

// 是否顯示 Collection 選擇器
const showCollectionSelector = computed(() => {
  return selectedGraph.value === 'rag_graph' || selectedGraph.value === 'regulation_graph'
})

// 是否可以確認
const canConfirm = computed(() => {
  // 必須選擇 Graph
  if (!selectedGraph.value) {
    return false
  }

  // 如果選擇 RAG Graph 或 Regulation Graph,必須選擇至少一個 Collection
  if ((selectedGraph.value === 'rag_graph' || selectedGraph.value === 'regulation_graph')
    && selectedCollections.value.length === 0) {
    return false
  }

  return true
})

// 動態計算 Modal 樣式（響應式寬度和高度）
const modalStyle = computed(() => {
  // 基礎樣式配置
  const baseWidth = width.value <= 768
    ? '90vw'
    : width.value <= 1024
      ? '60vw'
      : '50vw'

  const minWidth = width.value <= 768
    ? undefined
    : width.value <= 1024
      ? '500px'
      : '600px'

  const maxWidth = width.value <= 768 ? undefined : '1000px'

  // 動態高度：根據是否顯示 CollectionSelector 調整
  let maxHeight
  if (width.value <= 768) {
    maxHeight = '85vh'
  }
  else if (width.value <= 1024) {
    maxHeight = showCollectionSelector.value ? '85vh' : '80vh'
  }
  else {
    // 大螢幕：選擇 RAG agent 時增加高度
    maxHeight = showCollectionSelector.value ? '85vh' : '75vh'
  }

  return {
    width: baseWidth,
    minWidth,
    maxWidth,
    maxHeight,
  }
})

// Modal 內容區樣式（動態計算可用高度）
const contentStyle = computed<CSSProperties>(() => {
  const headerHeight = 64 // n-card__header
  const footerHeight = 74 // n-card__footer
  const totalReserved = headerHeight + footerHeight

  const baseHeight = showCollectionSelector.value ? '85vh' : '75vh'

  return {
    maxHeight: `calc(${baseHeight} - ${totalReserved}px)`,
    overflowY: 'auto',
    padding: '4px 24px',
  }
})

// 監聽 Graph 變更,清空 Collection 選擇
watch(selectedGraph, (newGraph, oldGraph) => {
  if (newGraph !== oldGraph && (newGraph === 'base_graph' || newGraph === 'agent_graph')) {
    selectedCollections.value = []
  }
})

// 監聽彈窗關閉,重置表單
watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})

// 重置表單
function resetForm() {
  selectedGraph.value = null
  selectedCollections.value = []
  sessionTitle.value = ''
}

// 關閉彈窗
function handleClose() {
  emit('update:show', false)
}

// 確認配置
function handleConfirm() {
  if (!canConfirm.value || !selectedGraph.value) {
    message.warning(t('chat.config.incomplete'))
    return
  }

  const config: SessionCreateRequest = {
    graph_type: selectedGraph.value,
    collection_ids: (selectedGraph.value === 'rag_graph' || selectedGraph.value === 'regulation_graph')
      ? selectedCollections.value
      : [],
  }

  // 只有在使用者填寫了標題時才傳遞 title
  const title = sessionTitle.value.trim()
  if (title) {
    config.title = title
  }

  emit('confirm', config)
  handleClose()
}
</script>

<template>
  <NModal
    :show="show"
    :mask-closable="false"
    preset="card"
    :title="t('chat.config.title')"
    :style="modalStyle"
    :content-style="contentStyle"
    @update:show="handleClose"
  >
    <div class="config-content">
      <!-- 對話標題 -->
      <div class="config-section">
        <div class="section-header">
          <NText strong>
            {{ t('chat.config.sessionTitle') }}
          </NText>
          <NText :depth="3" style="font-size: 0.8125rem">
            {{ t('chat.config.titleHint') }}
          </NText>
        </div>
        <NInput
          v-model:value="sessionTitle"
          :placeholder="t('chat.config.titlePlaceholder')"
          :maxlength="100"
          show-count
          clearable
        />
      </div>

      <NDivider style="margin: 8px 0" />

      <!-- Graph 選擇 -->
      <div class="config-section">
        <GraphSelector
          v-model="selectedGraph"
          :graphs="graphs"
          :loading="loading"
        />
      </div>

      <!-- Collection 選擇 -->
      <Transition name="slide-fade">
        <div v-if="showCollectionSelector" class="config-section">
          <NDivider style="margin: 8px 0" />
          <div class="section-header">
            <NText strong>
              {{ t('chat.config.selectCollection') }}
            </NText>
            <NText :depth="3" style="font-size: 0.8125rem">
              *{{ selectedGraph === 'regulation_graph' ? t('chat.config.requiredForRegulation') : t('chat.config.requiredForRag') }}
            </NText>
          </div>
          <CollectionSelector
            v-model="selectedCollections"
            :placeholder="t('chat.collectionSelector.placeholder')"
          />
        </div>
      </Transition>

      <!-- 配置說明 -->
      <div class="config-hint">
        <NText :depth="3" style="font-size: 0.8125rem; line-height: 1.6">
          {{ t('chat.config.tip') }}
        </NText>
      </div>
    </div>

    <template #footer>
      <NSpace justify="end" :size="12">
        <NButton @click="handleClose">
          {{ t('common.actions.cancel') }}
        </NButton>
        <NButton
          type="primary"
          :disabled="!canConfirm"
          :loading="loading"
          @click="handleConfirm"
        >
          {{ t('chat.config.createButton') }}
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.config-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-hint {
  padding: 8px 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%);
  border-radius: 8px;
  border-left: 3px solid #8b5cf6;
}

/* 動畫 */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .config-content {
    gap: 14px;
  }

  .config-section {
    gap: 8px;
  }
}
</style>
