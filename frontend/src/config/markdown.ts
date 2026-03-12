/**
 * Markdown 渲染配置
 * 集中管理 vue-renderer-markdown 的相關設定
 */

/**
 * Shiki 語法高亮配置
 */
export const shikiConfig = {
  // 主題配置 (支援淺色和深色模式)
  themes: {
    light: 'github-light',
    dark: 'github-dark',
  },

  // 支援的程式語言 (按需載入以優化效能)
  languages: [
    'python',
    'javascript',
    'typescript',
    'tsx',
    'jsx',
    'bash',
    'shell',
    'json',
    'yaml',
    'markdown',
    'html',
    'css',
    'scss',
    'sql',
    'dockerfile',
    'nginx',
    'go',
    'rust',
    'java',
    'cpp',
    'c',
  ],
}

/**
 * Markdown 渲染器配置
 */
export const markdownConfig = {
  // 是否啟用串流模式
  streaming: false,

  // 是否啟用數學公式支援 (需要安裝 katex)
  enableMath: false,

  // 是否啟用 Mermaid 圖表 (需要安裝 mermaid)
  enableMermaid: false,

  // 是否啟用語法高亮
  enableHighlight: true,

  // 安全配置
  security: {
    // 允許的連結協議
    allowedProtocols: ['http', 'https', 'mailto'],

    // 是否允許圖片
    allowImages: true,

    // 是否清理 HTML 標籤
    sanitizeHtml: true,
  },

  // 程式碼區塊配置
  codeBlock: {
    // 是否顯示行號
    showLineNumbers: false,

    // 是否顯示複製按鈕
    showCopyButton: true,

    // 是否顯示語言標籤
    showLanguage: true,
  },
}

/**
 * 預設配置匯出
 */
export default {
  shiki: shikiConfig,
  markdown: markdownConfig,
}
