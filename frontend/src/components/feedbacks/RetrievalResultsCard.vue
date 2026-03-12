<script setup lang="ts">
import type { RetrievalResult } from '@/types/chat'
import { NCard, NCollapse, NCollapseItem, NTag } from 'naive-ui'

defineProps<{
  results: RetrievalResult[]
}>()

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
  <NCard title="RAG 檢索結果">
    <template #header-extra>
      <NTag type="info" size="small">
        共 {{ results.length }} 條結果
      </NTag>
    </template>

    <NCollapse>
      <NCollapseItem
        v-for="(result, index) in results"
        :key="index"
        :title="`${index + 1}. ${result.metadata?.dataset_filename || result.filename || '未知文檔'}`"
      >
        <template #header-extra>
          <NTag :type="getScoreColor(result.score)" size="small">
            分數: {{ result.score.toFixed(4) }}
          </NTag>
        </template>

        <div class="retrieval-result-content">
          <div v-if="result.metadata?.collection_name" class="metadata-row">
            <span class="label">知識庫:</span>
            <NTag size="small" type="info">
              {{ result.metadata.collection_name }}
            </NTag>
          </div>

          <div class="content-section">
            <span class="label">內容:</span>
            <pre class="content-box">{{ result.content }}</pre>
          </div>

          <div v-if="result.metadata" class="metadata-section">
            <span class="label">元資料:</span>
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
