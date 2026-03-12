<script setup lang="ts">
import type { IssueTagCount } from '@/types/dashboard'
import { NEmpty, NTag } from 'naive-ui'

interface Props {
  tags: IssueTagCount[]
}

defineProps<Props>()
</script>

<template>
  <div class="issue-tag-list">
    <div v-if="tags.length > 0" class="tag-items">
      <div v-for="(item, index) in tags" :key="item.tag" class="tag-item">
        <div class="tag-rank">
          {{ index + 1 }}
        </div>
        <div class="tag-content">
          <NTag type="warning" :bordered="false" size="small">
            {{ item.tag }}
          </NTag>
        </div>
        <div class="tag-count">
          {{ item.count }} 次
        </div>
      </div>
    </div>
    <NEmpty v-else description="暫無問題標籤" size="small" />
  </div>
</template>

<style scoped>
.issue-tag-list {
  min-height: 100px;
}

.tag-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 8px;
  transition: background 0.2s;
}

.tag-item:hover {
  background: #f3f4f6;
}

.tag-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e5e7eb;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  flex-shrink: 0;
}

.tag-content {
  flex: 1;
  min-width: 0;
}

.tag-count {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  flex-shrink: 0;
}
</style>
