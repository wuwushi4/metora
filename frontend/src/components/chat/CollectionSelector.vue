<script setup lang="ts">
import type { SelectOption } from 'naive-ui'
import type { Collection } from '@/types/collection'
import { NSelect, NSpin, NTag, NText } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { getCollectionList } from '@/api/collections'
import { message } from '@/utils/message'

interface Props {
  modelValue: number[]
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '請選擇知識庫...',
})

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
}>()

const collections = ref<Collection[]>([])
const loading = ref(false)

const options = computed<SelectOption[]>(() => {
  return collections.value.map(collection => ({
    label: collection.name,
    value: collection.id,
    disabled: false,
  }))
})

const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => {
    emit('update:modelValue', value)
  },
})

async function loadCollections() {
  loading.value = true
  try {
    const response = await getCollectionList({
      page: 1,
      page_size: 100,
    })
    collections.value = response.items
  }
  catch (error) {
    console.error('載入知識庫列表失敗:', error)
    message.error('載入知識庫列表失敗')
  }
  finally {
    loading.value = false
  }
}

function renderLabel(option: SelectOption) {
  const collection = collections.value.find(c => c.id === option.value)
  if (!collection) {
    return option.label as string
  }

  return h('div', { class: 'collection-option' }, [
    h('span', { class: 'collection-name' }, collection.name),
    collection.description
      ? h(NText, { depth: 3, class: 'collection-description' }, {
          default: () => collection.description,
        })
      : null,
  ])
}

function renderTag({ option, handleClose }: { option: SelectOption, handleClose: () => void }) {
  const collection = collections.value.find(c => c.id === option.value)
  if (!collection) {
    return h(
      NTag,
      {
        type: 'info',
        closable: true,
        onClose: handleClose,
      },
      { default: () => option.label },
    )
  }

  return h(
    NTag,
    {
      type: 'info',
      closable: !props.disabled,
      onClose: handleClose,
    },
    {
      default: () => [
        h('span', collection.name),
        h(
          NText,
          { depth: 3, style: { marginLeft: '8px', fontSize: '0.75rem' } },
          { default: () => `(${collection.dataset_count} 個文檔)` },
        ),
      ],
    },
  )
}

onMounted(() => {
  loadCollections()
})

defineExpose({
  refresh: loadCollections,
})
</script>

<template>
  <div class="collection-selector">
    <NSelect
      v-model:value="selectedValue"
      multiple
      :options="options"
      :placeholder="placeholder"
      :disabled="disabled || loading"
      :loading="loading"
      :render-label="renderLabel"
      :render-tag="renderTag"
      :max-tag-count="3"
      clearable
      filterable
    >
      <template #empty>
        <div class="select-empty">
          <NText :depth="3">
            尚無可用的知識庫
          </NText>
        </div>
      </template>
    </NSelect>

    <!-- 載入中提示 -->
    <div v-if="loading" class="loading-hint">
      <NSpin size="small" />
      <NText :depth="3" style="font-size: 0.75rem">
        載入中...
      </NText>
    </div>

    <!-- 已選擇提示 -->
    <div v-if="selectedValue.length > 0 && !loading" class="selection-hint">
      <NText :depth="3" style="font-size: 0.75rem">
        已選擇 {{ selectedValue.length }} 個知識庫
      </NText>
    </div>
  </div>
</template>

<style scoped>
.collection-selector {
  width: 100%;
}

/* 選項樣式 */
:deep(.collection-option) {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

:deep(.collection-name) {
  font-weight: 500;
  font-size: 0.9375rem;
  color: #1f2937;
}

:deep(.collection-description) {
  font-size: 0.8125rem;
  line-height: 1.4;
  color: #6b7280;
}

/* 空狀態 */
.select-empty {
  padding: 12px;
  text-align: center;
}

/* 載入提示 */
.loading-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  color: #6b7280;
}

/* 已選擇提示 */
.selection-hint {
  margin-top: 6px;
  color: #6b7280;
}

/* 深色模式支援 */
@media (prefers-color-scheme: dark) {
  :deep(.collection-name) {
    color: #f9fafb;
  }

  :deep(.collection-description) {
    color: #9ca3af;
  }
}
</style>
