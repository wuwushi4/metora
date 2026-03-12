<script setup lang="ts">
import MarkdownRender from 'vue-renderer-markdown'

interface Props {
  content: string
}

defineProps<Props>()
</script>

<template>
  <div class="message-text markdown-content">
    <MarkdownRender :content="content" />
  </div>
</template>

<style scoped>
.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.9375rem;
}

/* Markdown 內容樣式 */
.markdown-content {
  line-height: 1.7;
  word-wrap: break-word;
}

/* Markdown 渲染器的深層樣式覆寫 */
.markdown-content :deep(.markdown-body) {
  font-size: 0.9375rem;
  color: inherit;
  background: transparent;
}

/* 段落 */
.markdown-content :deep(p) {
  margin: 0.75em 0;
  line-height: 1.7;
}

.markdown-content :deep(p:first-child) {
  margin-top: 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

/* 標題 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin: 1.2em 0 0.6em;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 1.75em;
}
.markdown-content :deep(h2) {
  font-size: 1.5em;
}
.markdown-content :deep(h3) {
  font-size: 1.25em;
}
.markdown-content :deep(h4) {
  font-size: 1.1em;
}
.markdown-content :deep(h5) {
  font-size: 1em;
}
.markdown-content :deep(h6) {
  font-size: 0.95em;
}

/* 清單 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.75em 0;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin: 0.3em 0;
  line-height: 1.6;
}

.markdown-content :deep(ul ul),
.markdown-content :deep(ol ul),
.markdown-content :deep(ul ol),
.markdown-content :deep(ol ol) {
  margin: 0.25em 0;
}

/* 程式碼區塊 (pre + code) */
.markdown-content :deep(pre) {
  margin: 1em 0;
  padding: 1.25em;
  border-radius: 8px;
  overflow-x: auto;
  background: #282c34 !important; /* VS Code Dark+ 主題背景 */
  border: 1px solid #3e4451;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.markdown-content :deep(pre code) {
  background: transparent !important;
  padding: 0 !important;
  border-radius: 0;
  border: none !important;
  font-size: 0.875em;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  /* VS Code Dark+ 主題預設文字顏色 - 淺灰白色 */
  color: #abb2bf !important;
}

/* 行內程式碼 (僅 code 不在 pre 內) */
.markdown-content :deep(:not(pre) > code) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875em;
  padding: 0.2em 0.4em;
  background: #f3f4f6;
  border-radius: 4px;
  color: #e11d48;
  border: 1px solid #e5e7eb;
  font-weight: 500;
}

/* 引用區塊 */
.markdown-content :deep(blockquote) {
  margin: 1em 0;
  padding: 0.5em 0 0.5em 1em;
  border-left: 4px solid #8b5cf6;
  background: #f9fafb;
  color: #6b7280;
  border-radius: 0 4px 4px 0;
}

.markdown-content :deep(blockquote p) {
  margin: 0.5em 0;
}

/* 表格 */
.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5em 0.75em;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.markdown-content :deep(tr:nth-child(even)) {
  background: #fafafa;
}

/* 水平分隔線 */
.markdown-content :deep(hr) {
  margin: 1.5em 0;
  border: none;
  border-top: 2px solid #e5e7eb;
}

/* 連結 */
.markdown-content :deep(a) {
  color: #3b82f6;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s;
}

.markdown-content :deep(a:hover) {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

/* 粗體 */
.markdown-content :deep(strong) {
  font-weight: 600;
  color: #1f2937;
}

/* 斜體 */
.markdown-content :deep(em) {
  font-style: italic;
  color: #4b5563;
}

/* 刪除線 */
.markdown-content :deep(del) {
  text-decoration: line-through;
  color: #9ca3af;
}

/* 任務清單 */
.markdown-content :deep(input[type='checkbox']) {
  margin-right: 0.5em;
}

/* 圖片 */
.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 0.75em 0;
}
</style>
