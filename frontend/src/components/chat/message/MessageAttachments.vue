<script setup lang="ts">
import type { MessageAttachment } from '@/types/upload'
import { NImage } from 'naive-ui'
import { getAttachmentUrl } from '@/api/chat'

interface Props {
  attachments: MessageAttachment[]
  messageId: string
}

defineProps<Props>()
</script>

<template>
  <div class="message-attachments">
    <div class="attachments-grid">
      <div
        v-for="attachment in attachments"
        :key="attachment.id"
        class="attachment-item"
      >
        <!-- 圖片附件 -->
        <NImage
          v-if="attachment.attachment_type === 'image'"
          :src="getAttachmentUrl(messageId, attachment.id)"
          :alt="attachment.original_filename"
          object-fit="cover"
          class="attachment-image"
          :preview-src="getAttachmentUrl(messageId, attachment.id)"
        />

        <!-- PDF 頁面附件 -->
        <div
          v-else-if="attachment.attachment_type === 'pdf_page'"
          class="pdf-attachment"
        >
          <NImage
            :src="getAttachmentUrl(messageId, attachment.id)"
            :alt="`${attachment.original_filename} - 第 ${attachment.extra_data?.page_number} 頁`"
            object-fit="cover"
            class="attachment-image"
            :preview-src="getAttachmentUrl(messageId, attachment.id)"
          />
          <!-- 頁碼標籤 -->
          <div class="pdf-page-label">
            <span class="page-info">
              第 {{ attachment.extra_data?.page_number }}/{{ attachment.extra_data?.total_pages }} 頁
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-attachments {
  margin-bottom: 12px;
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.attachment-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  aspect-ratio: 1;
}

.attachment-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.attachment-image:hover {
  transform: scale(1.05);
}

/* PDF 附件 */
.pdf-attachment {
  position: relative;
  width: 100%;
  height: 100%;
}

.pdf-page-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-info {
  font-size: 11px;
  font-weight: 600;
  color: white;
  letter-spacing: 0.3px;
}
</style>
