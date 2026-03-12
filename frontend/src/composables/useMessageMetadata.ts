import type { ChatMessage } from '@/types/chat'
import { computed } from 'vue'

export function useMessageMetadata(message: ChatMessage, isLastMessage: boolean = false, isStreaming: boolean = false) {
  // 判斷是否有附件
  const hasAttachments = computed(() => {
    return message.attachments
      && Array.isArray(message.attachments)
      && message.attachments.length > 0
  })

  // 判斷是否有檢索結果
  const hasRetrievalResults = computed(() => {
    return message.metadata?.retrieval_results
      && Array.isArray(message.metadata.retrieval_results)
      && message.metadata.retrieval_results.length > 0
  })

  // 判斷是否有子查詢
  const hasSubQueries = computed(() => {
    return message.metadata?.sub_queries
      && Array.isArray(message.metadata.sub_queries)
      && message.metadata.sub_queries.length > 0
  })

  // 判斷是否有重寫查詢（regulation_graph）
  const hasRewrittenQueries = computed(() => {
    return message.metadata?.rewritten_queries
      && Array.isArray(message.metadata.rewritten_queries)
      && message.metadata.rewritten_queries.length > 0
  })

  // 判斷是否有目標條文（regulation_graph）
  const hasTargetArticles = computed(() => {
    return message.metadata?.target_articles
      && Array.isArray(message.metadata.target_articles)
      && message.metadata.target_articles.length > 0
  })

  // 判斷是否有相關條文（regulation_graph）
  const hasRelatedArticles = computed(() => {
    return message.metadata?.related_articles
      && Array.isArray(message.metadata.related_articles)
      && message.metadata.related_articles.length > 0
  })

  // 判斷是否有工具輸出檔案
  const hasToolOutputFiles = computed(() => {
    return message.metadata?.tool_results
      && Array.isArray(message.metadata.tool_results)
      && message.metadata.tool_results.some(
        result => Array.isArray(result.output_files) && result.output_files.length > 0,
      )
  })

  // 判斷是否需要顯示 metadata 區塊
  const hasMetadata = computed(() => {
    return hasRetrievalResults.value
      || hasSubQueries.value
      || hasRewrittenQueries.value
      || hasTargetArticles.value
      || hasRelatedArticles.value
      || message.metadata?.processing_time
      || message.metadata?.query_type
  })

  // 判斷是否應該顯示反饋按鈕（只對 assistant 訊息，且不在串流中）
  const shouldShowFeedback = computed(() => {
    if (message.role !== 'assistant')
      return false
    // 如果是最後一條訊息且正在串流，則不顯示
    if (isLastMessage && isStreaming)
      return false
    return true
  })

  return {
    hasAttachments,
    hasRetrievalResults,
    hasSubQueries,
    hasRewrittenQueries,
    hasTargetArticles,
    hasRelatedArticles,
    hasToolOutputFiles,
    hasMetadata,
    shouldShowFeedback,
  }
}
