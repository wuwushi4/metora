import type {
  PromptTemplate,
  PromptTemplateCreateRequest,
  PromptTemplateUpdateRequest,
} from '@/types/prompt'
/**
 * Prompts Store
 * 管理提示詞模板的狀態
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as promptsApi from '@/api/prompts'
import { message } from '@/utils/message'

export const usePromptsStore = defineStore('prompts', () => {
  // ==================== State ====================

  const templates = ref<PromptTemplate[]>([])

  const loadingStates = ref({
    loading: false,
    creating: false,
    updating: false,
    deleting: false,
  })

  // ==================== Getters ====================

  /**
   * 取得收藏的提示詞模板列表
   */
  const favoriteTemplates = computed(() => {
    return templates.value.filter(t => t.is_favorite && t.is_active)
  })

  /**
   * 取得啟用的提示詞模板列表
   */
  const activeTemplates = computed(() => {
    return templates.value.filter(t => t.is_active)
  })

  /**
   * 是否正在載入
   */
  const isLoading = computed(() =>
    Object.values(loadingStates.value).some(v => v),
  )

  // ==================== Actions ====================

  /**
   * 載入使用者的所有提示詞模板
   */
  async function loadTemplates() {
    loadingStates.value.loading = true
    try {
      const response = await promptsApi.getPromptTemplates({
        page: 1,
        pageSize: 100,
        is_active: true,
      })
      templates.value = response.items
    }
    catch (error) {
      console.error('載入提示詞模板失敗:', error)
      message.error('載入提示詞模板失敗')
      throw error
    }
    finally {
      loadingStates.value.loading = false
    }
  }

  /**
   * 建立新的提示詞模板
   */
  async function createTemplate(data: PromptTemplateCreateRequest) {
    loadingStates.value.creating = true
    try {
      const newTemplate = await promptsApi.createPromptTemplate(data)
      templates.value.unshift(newTemplate)

      message.success('建立提示詞模板成功')
      return newTemplate
    }
    catch (error) {
      console.error('建立提示詞模板失敗:', error)
      message.error('建立提示詞模板失敗')
      throw error
    }
    finally {
      loadingStates.value.creating = false
    }
  }

  /**
   * 更新提示詞模板
   */
  async function updateTemplate(id: string, data: PromptTemplateUpdateRequest) {
    loadingStates.value.updating = true
    try {
      const updatedTemplate = await promptsApi.updatePromptTemplate(id, data)

      // 更新列表中的模板
      const index = templates.value.findIndex(t => t.id === id)
      if (index !== -1) {
        templates.value[index] = updatedTemplate
      }

      message.success('更新提示詞模板成功')
      return updatedTemplate
    }
    catch (error) {
      console.error('更新提示詞模板失敗:', error)
      message.error('更新提示詞模板失敗')
      throw error
    }
    finally {
      loadingStates.value.updating = false
    }
  }

  /**
   * 刪除提示詞模板（軟刪除）
   */
  async function deleteTemplate(id: string) {
    loadingStates.value.deleting = true
    try {
      await promptsApi.deletePromptTemplate(id)

      // 從列表中移除
      templates.value = templates.value.filter(t => t.id !== id)

      message.success('刪除提示詞模板成功')
    }
    catch (error) {
      console.error('刪除提示詞模板失敗:', error)
      message.error('刪除提示詞模板失敗')
      throw error
    }
    finally {
      loadingStates.value.deleting = false
    }
  }

  /**
   * 切換收藏狀態
   */
  async function toggleFavorite(id: string) {
    loadingStates.value.updating = true
    try {
      const updatedTemplate = await promptsApi.toggleFavorite(id)

      // 更新列表中的模板狀態
      const index = templates.value.findIndex(t => t.id === id)
      if (index !== -1) {
        templates.value[index] = updatedTemplate
      }

      const action = updatedTemplate.is_favorite ? '收藏' : '取消收藏'
      message.success(`${action}提示詞成功`)
      return updatedTemplate
    }
    catch (error) {
      console.error('切換收藏狀態失敗:', error)
      message.error('操作失敗')
      throw error
    }
    finally {
      loadingStates.value.updating = false
    }
  }

  /**
   * 根據 ID 取得提示詞模板
   */
  function getTemplateById(id: string): PromptTemplate | undefined {
    return templates.value.find(t => t.id === id)
  }

  /**
   * 清空狀態（用於登出）
   */
  function clearState() {
    templates.value = []
    loadingStates.value = {
      loading: false,
      creating: false,
      updating: false,
      deleting: false,
    }
  }

  return {
    // State
    templates,
    loadingStates,

    // Getters
    favoriteTemplates,
    activeTemplates,
    isLoading,

    // Actions
    loadTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    toggleFavorite,
    getTemplateById,
    clearState,
  }
})
