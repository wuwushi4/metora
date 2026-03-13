/**
 * 檔案處理工具函數
 */

import type {
  AttachmentType,
  FilePreview,
  FileValidationError,
  FileValidationRules,
} from '@/types/upload'
import i18n from '@/i18n'

const { t } = i18n.global

/**
 * 預設檔案驗證規則
 */
export const DEFAULT_FILE_RULES: FileValidationRules = {
  maxFiles: 5,
  maxSize: 50 * 1024 * 1024, // 50MB (支援 PDF 和 Excel)
  allowedFormats: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'pdf', 'xlsx', 'xls', 'csv', 'docx'],
  allowedMimeTypes: [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
    'application/vnd.ms-excel', // .xls
    'text/csv', // .csv
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  ],
}

/**
 * 從檔案名稱取得副檔名
 */
export function getFileExtension(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  return ext || ''
}

/**
 * 根據副檔名判斷附件類型
 */
export function getAttachmentType(filename: string): AttachmentType {
  const ext = getFileExtension(filename)
  const imageFormats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
  const spreadsheetFormats = ['xlsx', 'xls', 'csv']
  const documentFormats = ['docx']

  if (imageFormats.includes(ext)) {
    return 'image'
  }

  if (ext === 'pdf') {
    return 'pdf_page'
  }

  if (spreadsheetFormats.includes(ext) || documentFormats.includes(ext)) {
    return 'file'
  }

  return 'image' // 預設
}

/**
 * 驗證單個檔案
 */
export function validateFile(
  file: File,
  rules: FileValidationRules = DEFAULT_FILE_RULES,
): FileValidationError | null {
  // 檢查檔案大小
  if (file.size > rules.maxSize) {
    return {
      type: 'FILE_TOO_LARGE',
      message: t('fileUtils.fileTooLarge', { name: file.name, size: formatFileSize(rules.maxSize) }),
      filename: file.name,
    }
  }

  // 檢查 MIME 類型
  if (!rules.allowedMimeTypes.includes(file.type)) {
    return {
      type: 'INVALID_FORMAT',
      message: t('fileUtils.invalidFormat', { name: file.name, type: file.type }),
      filename: file.name,
    }
  }

  // 檢查副檔名
  const ext = getFileExtension(file.name)
  if (!rules.allowedFormats.includes(ext)) {
    return {
      type: 'INVALID_FORMAT',
      message: t('fileUtils.invalidExtension', { name: file.name, ext }),
      filename: file.name,
    }
  }

  return null
}

/**
 * 驗證檔案列表
 */
export function validateFiles(
  files: File[],
  rules: FileValidationRules = DEFAULT_FILE_RULES,
): FileValidationError | null {
  // 檢查檔案數量
  if (files.length > rules.maxFiles) {
    return {
      type: 'TOO_MANY_FILES',
      message: t('fileUtils.tooManyFiles', { max: rules.maxFiles }),
      filename: '',
    }
  }

  // 逐個驗證檔案
  for (const file of files) {
    const error = validateFile(file, rules)
    if (error) {
      return error
    }
  }

  return null
}

/**
 * 生成檔案預覽物件
 */
export function createFilePreview(file: File): FilePreview {
  return {
    id: generateFileId(file),
    file,
    previewUrl: URL.createObjectURL(file),
    type: getAttachmentType(file.name),
    status: 'pending',
  }
}

/**
 * 生成檔案唯一 ID
 */
export function generateFileId(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}-${Date.now()}`
}

/**
 * 釋放檔案預覽 URL
 */
export function revokeFilePreview(preview: FilePreview): void {
  if (preview.previewUrl) {
    URL.revokeObjectURL(preview.previewUrl)
  }
}

/**
 * 格式化檔案大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0)
    return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`
}

/**
 * 檢查是否為圖片檔案
 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

/**
 * 檢查是否為 PDF 檔案
 */
export function isPDFFile(file: File): boolean {
  return file.type === 'application/pdf'
}

/**
 * 建立 FormData (用於 multipart/form-data 上傳)
 */
export function createMessageFormData(
  content: string,
  files: File[],
  promptTemplateId?: string | null,
): FormData {
  const formData = new FormData()

  // 添加文字內容
  formData.append('content', content)

  // 添加檔案
  files.forEach((file) => {
    formData.append('files', file)
  })

  // 添加提示詞模板 ID（如果有）
  if (promptTemplateId) {
    formData.append('prompt_template_id', promptTemplateId)
  }

  return formData
}

/**
 * 從拖放事件取得檔案列表
 */
export function getFilesFromDragEvent(event: DragEvent): File[] {
  const files: File[] = []

  if (event.dataTransfer?.files) {
    Array.from(event.dataTransfer.files).forEach((file) => {
      files.push(file)
    })
  }

  return files
}

/**
 * 壓縮圖片 (使用 Canvas)
 *
 * @param file 原始圖片檔案
 * @param maxWidth 最大寬度
 * @param maxHeight 最大高度
 * @param quality 壓縮品質 (0-1)
 * @returns Promise<File>
 */
export function compressImage(
  file: File,
  maxWidth: number = 1920,
  maxHeight: number = 1080,
  quality: number = 0.85,
): Promise<File> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        const canvas = document.createElement('canvas')
        let { width, height } = img

        // 計算縮放比例
        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width = width * ratio
          height = height * ratio
        }

        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Canvas context unavailable'))
          return
        }

        // 繪製圖片
        ctx.drawImage(img, 0, 0, width, height)

        // 轉換為 Blob
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error(t('fileUtils.compressFailed')))
              return
            }

            // 建立新的 File 物件
            const compressedFile = new File([blob], file.name, {
              type: 'image/jpeg',
              lastModified: Date.now(),
            })

            resolve(compressedFile)
          },
          'image/jpeg',
          quality,
        )
      }

      img.onerror = () => {
        reject(new Error(t('fileUtils.imageLoadFailed')))
      }

      img.src = e.target?.result as string
    }

    reader.onerror = () => {
      reject(new Error(t('fileUtils.fileReadFailed')))
    }

    reader.readAsDataURL(file)
  })
}
