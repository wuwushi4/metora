<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'
import { NCard, NCollapse, NCollapseItem, NSpace, NTag, NText } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useMessageMetadata } from '@/composables/useMessageMetadata'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const { t } = useI18n()

const {
  hasRetrievalResults,
  hasSubQueries,
  hasRewrittenQueries,
  hasTargetArticles,
  hasRelatedArticles,
} = useMessageMetadata(props.message)

// 格式化處理時間
function formatProcessingTime(ms: number): string {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`
  }
  return `${(ms / 1000).toFixed(2)}s`
}

// 截斷文字用於預覽
function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) {
    return text
  }
  return `${text.slice(0, maxLength)}...`
}
</script>

<template>
  <div class="message-metadata">
    <NCollapse arrow-placement="right">
      <!-- 檢索結果 -->
      <NCollapseItem
        v-if="hasRetrievalResults"
        name="retrieval"
        :title="t('chat.metadata.retrievalResults')"
      >
        <NSpace vertical :size="12">
          <NCard
            v-for="(result, index) in message.metadata?.retrieval_results"
            :key="index"
            size="small"
            :bordered="true"
            class="retrieval-result-card"
          >
            <div class="result-header">
              <NSpace align="center" :size="8">
                <NTag :bordered="false" type="info" size="small">
                  {{ t('chat.metadata.source', { n: index + 1 }) }}
                </NTag>
                <NText class="result-filename" :depth="3">
                  {{ result.filename }}
                </NText>
                <NTag
                  :bordered="false"
                  :type="result.score >= 0.8 ? 'success' : result.score >= 0.5 ? 'warning' : 'default'"
                  size="small"
                >
                  {{ t('chat.metadata.relevance', { score: (result.score * 100).toFixed(1) }) }}
                </NTag>
              </NSpace>
            </div>
            <div class="result-content">
              <NText :depth="2" class="content-snippet">
                {{ truncateText(result.content, 150) }}
              </NText>
            </div>
          </NCard>
        </NSpace>
      </NCollapseItem>

      <!-- 子查詢 (RAG Graph) -->
      <NCollapseItem
        v-if="hasSubQueries"
        name="sub_queries"
        :title="t('chat.metadata.queryRewrite')"
      >
        <NSpace vertical :size="8">
          <div
            v-for="(subQuery, index) in message.metadata?.sub_queries"
            :key="index"
            class="sub-query-item"
          >
            <NSpace align="center" :size="8">
              <NTag :bordered="false" type="primary" size="small">
                Q{{ index + 1 }}
              </NTag>
              <NText>{{ typeof subQuery === 'string' ? subQuery : subQuery.rewritten }}</NText>
            </NSpace>
          </div>
        </NSpace>
      </NCollapseItem>

      <!-- 查詢重構 (Regulation Graph) -->
      <NCollapseItem
        v-if="hasTargetArticles || hasRewrittenQueries"
        name="query_rewrite"
        :title="t('chat.metadata.queryRestructure')"
      >
        <NSpace vertical :size="12">
          <!-- 目標條文 -->
          <div v-if="hasTargetArticles" class="regulation-section">
            <NText strong style="font-size: 0.875rem">
              {{ t('chat.metadata.targetArticles') }}
            </NText>
            <NSpace :size="8" style="margin-top: 8px">
              <NTag
                v-for="(article, index) in message.metadata?.target_articles"
                :key="index"
                :bordered="false"
                type="success"
                size="small"
              >
                {{ t('chat.metadata.articleNumber', { n: article }) }}
              </NTag>
            </NSpace>
          </div>

          <!-- 重寫查詢 -->
          <div v-if="hasRewrittenQueries" class="regulation-section">
            <NText strong style="font-size: 0.875rem">
              {{ t('chat.metadata.rewrittenQueries') }}
            </NText>
            <NSpace vertical :size="8" style="margin-top: 8px">
              <div
                v-for="(query, index) in message.metadata?.rewritten_queries"
                :key="index"
                class="sub-query-item"
              >
                <NSpace align="center" :size="8">
                  <NTag :bordered="false" type="primary" size="small">
                    Q{{ Number(index) + 1 }}
                  </NTag>
                  <NText>{{ query }}</NText>
                </NSpace>
              </div>
            </NSpace>
          </div>
        </NSpace>
      </NCollapseItem>

      <!-- 相關條文 (Regulation Graph) -->
      <NCollapseItem
        v-if="hasRelatedArticles"
        name="related_articles"
        :title="t('chat.metadata.citationRelationships')"
      >
        <NSpace vertical :size="12">
          <NCard
            v-for="(article, index) in message.metadata?.related_articles"
            :key="index"
            size="small"
            :bordered="true"
            class="retrieval-result-card"
          >
            <div class="result-header">
              <NSpace align="center" :size="8">
                <NTag :bordered="false" type="warning" size="small">
                  {{ t('chat.metadata.relatedArticle', { n: Number(index) + 1 }) }}
                </NTag>
                <NText class="result-filename" :depth="3">
                  {{ article.metadata?.article_num ? t('chat.metadata.articleNumber', { n: article.metadata.article_num }) : t('chat.metadata.unknownArticle') }}
                </NText>
                <NTag
                  v-if="article.score"
                  :bordered="false"
                  :type="article.score >= 0.8 ? 'success' : article.score >= 0.5 ? 'warning' : 'default'"
                  size="small"
                >
                  {{ t('chat.metadata.relevance', { score: (article.score * 100).toFixed(1) }) }}
                </NTag>
              </NSpace>
            </div>
            <div class="result-content">
              <NText :depth="2" class="content-snippet">
                {{ truncateText(article.content, 150) }}
              </NText>
            </div>
          </NCard>
        </NSpace>
      </NCollapseItem>

      <!-- 處理時間與其他資訊 -->
      <NCollapseItem
        v-if="message.metadata?.processing_time || message.metadata?.need_rag !== undefined || message.metadata?.query_type || message.metadata?.intent_reason"
        name="stats"
        :title="t('chat.metadata.processingInfo')"
      >
        <NSpace vertical :size="8">
          <div v-if="message.metadata?.query_type" class="stat-item">
            <NText :depth="3">
              {{ t('chat.metadata.queryType') }}
            </NText>
            <NTag :bordered="false" type="info" size="small">
              {{ t(`chat.metadata.queryTypes.${message.metadata.query_type}`, message.metadata.query_type) }}
            </NTag>
          </div>
          <div v-if="message.metadata?.intent_reason" class="stat-item">
            <NText :depth="3">
              {{ t('chat.metadata.intentAnalysis') }}
            </NText>
            <NText>{{ message.metadata.intent_reason }}</NText>
          </div>
          <div v-if="message.metadata?.need_rag !== undefined" class="stat-item">
            <NText :depth="3">
              {{ t('chat.metadata.retrievalMode') }}
            </NText>
            <NTag :bordered="false" :type="message.metadata.need_rag ? 'info' : 'default'" size="small">
              {{ message.metadata.need_rag ? t('chat.metadata.ragRetrieval') : t('chat.metadata.directAnswer') }}
            </NTag>
          </div>
          <div v-if="message.metadata?.processing_time" class="stat-item">
            <NText :depth="3">
              {{ t('chat.metadata.processingTime') }}
            </NText>
            <NTag :bordered="false" size="small">
              {{ formatProcessingTime(message.metadata.processing_time) }}
            </NTag>
          </div>
        </NSpace>
      </NCollapseItem>
    </NCollapse>
  </div>
</template>

<style scoped>
.message-metadata {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

/* 檢索結果卡片 */
.retrieval-result-card {
  background: #f9fafb;
}

.result-header {
  margin-bottom: 8px;
}

.result-filename {
  font-size: 0.875rem;
  font-weight: 500;
}

.result-content {
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.content-snippet {
  font-size: 0.8125rem;
  line-height: 1.5;
  display: block;
}

/* 子查詢項目 */
.sub-query-item {
  padding: 8px 12px;
  background: linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%);
  border-radius: 6px;
  border-left: 3px solid #8b5cf6;
}

/* 統計資訊項目 */
.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
}

/* 法規專用區塊 */
.regulation-section {
  padding: 12px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-radius: 8px;
  border-left: 3px solid #10b981;
}
</style>
