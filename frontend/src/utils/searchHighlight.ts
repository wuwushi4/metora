/**
 * 搜尋高亮工具函數
 *
 * 提供安全的文本高亮功能，防止 XSS 攻擊
 */
import DOMPurify from 'dompurify'

/**
 * 高亮搜尋關鍵字
 *
 * 將文本中的關鍵字用 <mark> 標籤包裹，並使用 DOMPurify 清理 HTML
 *
 * @param text - 原始文本
 * @param keyword - 搜尋關鍵字
 * @param maxKeywordLength - 關鍵字最大長度（預設 100，防止 ReDoS 攻擊）
 * @returns 高亮後的 HTML 字串（已清理）
 *
 * @example
 * ```typescript
 * const result = highlightKeyword('這是一個測試文本', '測試')
 * // 返回: '這是一個<mark class="search-highlight">測試</mark>文本'
 * ```
 */
export function highlightKeyword(
  text: string,
  keyword: string,
  maxKeywordLength: number = 100,
): string {
  if (!keyword.trim())
    return text

  // 限制關鍵字長度（防止 ReDoS）
  const trimmedKeyword = keyword.trim().slice(0, maxKeywordLength)

  // 轉義正則表達式特殊字元
  const escaped = trimmedKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')

  // 替換關鍵字為 <mark> 標籤
  const highlighted = text.replace(regex, '<mark class="search-highlight">$1</mark>')

  // 使用 DOMPurify 清理 HTML（嚴格模式）
  return DOMPurify.sanitize(highlighted, {
    ALLOWED_TAGS: ['mark'],
    ALLOWED_ATTR: ['class'],
    KEEP_CONTENT: true,
  })
}

/**
 * 批量高亮多個文本
 *
 * @param texts - 文本陣列
 * @param keyword - 搜尋關鍵字
 * @returns 高亮後的 HTML 字串陣列
 *
 * @example
 * ```typescript
 * const results = highlightKeywords(['文本1', '文本2'], '文本')
 * // 返回: ['<mark>文本</mark>1', '<mark>文本</mark>2']
 * ```
 */
export function highlightKeywords(
  texts: string[],
  keyword: string,
): string[] {
  return texts.map(text => highlightKeyword(text, keyword))
}

/**
 * 從文本中提取包含關鍵字的片段
 *
 * @param text - 原始文本
 * @param keyword - 搜尋關鍵字
 * @param maxLength - 片段最大長度（預設 100）
 * @returns 包含關鍵字的片段（帶省略號）
 *
 * @example
 * ```typescript
 * const snippet = extractSnippet('這是一個很長的文本，包含關鍵字測試', '測試', 20)
 * // 返回: '...包含關鍵字測試'
 * ```
 */
export function extractSnippet(
  text: string,
  keyword: string,
  maxLength: number = 100,
): string {
  const keywordLower = keyword.toLowerCase()
  const textLower = text.toLowerCase()

  const idx = textLower.indexOf(keywordLower)
  if (idx === -1) {
    // 找不到關鍵字，返回開頭
    return text.length > maxLength
      ? `${text.slice(0, maxLength)}...`
      : text
  }

  // 以關鍵字為中心，向前後各取一半
  const halfLength = Math.floor(maxLength / 2)
  const start = Math.max(0, idx - halfLength)
  const end = Math.min(text.length, idx + keyword.length + halfLength)

  let snippet = text.slice(start, end)

  // 添加省略號
  if (start > 0) {
    snippet = `...${snippet}`
  }
  if (end < text.length) {
    snippet = `${snippet}...`
  }

  return snippet
}

/**
 * 從文本中提取多個片段並高亮
 *
 * @param texts - 文本陣列
 * @param keyword - 搜尋關鍵字
 * @param maxLength - 每個片段最大長度
 * @param maxSnippets - 最大片段數量（預設 2）
 * @returns 高亮後的片段陣列
 */
export function extractAndHighlightSnippets(
  texts: string[],
  keyword: string,
  maxLength: number = 100,
  maxSnippets: number = 2,
): string[] {
  const snippets = texts
    .slice(0, maxSnippets)
    .map(text => extractSnippet(text, keyword, maxLength))
    .map(snippet => highlightKeyword(snippet, keyword))

  return snippets
}
