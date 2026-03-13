<script setup lang="ts">
import type { RetrievalResult } from '@/types/chat'
import { NCard, NCollapse, NCollapseItem, NTag } from 'naive-ui'
import { useI18n } from 'vue-i18n'

defineProps<{
  results: RetrievalResult[]
}>()

const { t } = useI18n()

function getScoreColor(score: number): 'success' | 'info' | 'warning' | 'error' {
  if (score >= 0.8)
    return 'success'
  if (score >= 0.6)
    return 'info'
  if (score >= 0.4)
    return 'warning'
  return 'error'
}
</script>

<template>
  <NCard :title="$t('feedbacks.retrieval.title')">
    <template #header-extra>
      <NTag type="info" size="small">
        {{ $t('feedbacks.retrieval.totalResults', { count: results.length }) }}
      </NTag>
    </template>

    <NCollapse>
      <NCollapseItem
        v-for="(result, index) in results"
        :key="index"
        :title="`${index + 1}. ${result.metadata?.dataset_filename || result.filename || t('feedbacks.retrieval.unknownDoc')}`"
      >
        <template #header-extra>
          <NTag :type="getScoreColor(result.score)" size="small">
            {{ $t('feedbacks.retrieval.score') }}: {{ result.score.toFixed(4) }}
          </NTag>
        </template>

        <div class="retrieval-result-content">
          <div v-if="result.metadata?.collection_name" class="metadata-row">
            <span class="label">{{ $t('feedbacks.retrieval.collectionLabel') }}:</span>
            <NTag size="small" type="info">
              {{ result.metadata.collection_name }}
            </NTag>
          </div>

          <div class="content-section">
            <span class="label">{{ $t('feedbacks.retrieval.contentLabel') }}:</span>
            <pre class="content-box">{{ result.content }}</pre>
          </div>

          <div v-if="result.metadata" class="metadata-section">
            <span class="label">{{ $t('feedbacks.retrieval.metadataLabel') }}:</span>
            <pre class="metadata-box">{{ JSON.stringify(result.metadata, null, 2) }}</pre>
          </div>
        </div>
      </NCollapseItem>
    </NCollapse>
  </NCard>
</template>

<style scoped>
.retrieval-result-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metadata-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content-section,
.metadata-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label {
  font-weight: 600;
  color: var(--n-text-color);
  font-size: 14px;
}

.content-box,
.metadata-box {
  margin: 0;
  padding: 12px;
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  color: #333;
}

.metadata-box {
  background-color: #fafafa;
}
</style>
