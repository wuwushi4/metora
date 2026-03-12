/**
 * 檔案下載 Composable
 * 提供從文字內容建立並下載檔案的功能
 */

/**
 * 下載文字內容為檔案
 *
 * @param content - 檔案內容
 * @param filename - 檔案名稱
 * @param mimeType - MIME 類型
 */
export function downloadTextAsFile(
  content: string,
  filename: string,
  mimeType = 'text/plain',
): void {
  // 建立 Blob 物件
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` })

  // 建立下載連結
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename

  // 觸發下載
  document.body.appendChild(link)
  link.click()

  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 下載 JSON 物件為檔案
 *
 * @param jsonObject - JSON 物件
 * @param filename - 檔案名稱
 */
export function downloadJsonAsFile(
  jsonObject: Record<string, any>,
  filename: string,
): void {
  const jsonString = JSON.stringify(jsonObject, null, 2)
  downloadTextAsFile(jsonString, filename, 'application/json')
}

/**
 * 下載 Markdown 內容為檔案
 *
 * @param markdown - Markdown 內容
 * @param filename - 檔案名稱
 */
export function downloadMarkdownAsFile(
  markdown: string,
  filename: string,
): void {
  downloadTextAsFile(markdown, filename, 'text/markdown')
}

/**
 * 檔案下載 Hook
 */
export function useFileDownload() {
  return {
    downloadTextAsFile,
    downloadJsonAsFile,
    downloadMarkdownAsFile,
  }
}
