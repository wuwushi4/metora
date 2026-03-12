<script setup lang="ts">
import { useBreakpoints } from '@vueuse/core'
import { NLayout, NLayoutContent } from 'naive-ui'
import { onMounted, ref, watch } from 'vue'
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const collapsed = ref(false)

const breakpoints = useBreakpoints({ mobile: 768 })
const isMobile = breakpoints.smaller('mobile')

// 行動端預設收合 sidebar
watch(isMobile, (mobile) => {
  collapsed.value = mobile
}, { immediate: true })

onMounted(() => {
  // 初始化認證狀態
  authStore.initAuth()
})
</script>

<template>
  <NLayout has-sider class="main-layout">
    <Sidebar :collapsed="collapsed" :is-mobile="isMobile" />
    <!-- 行動端遮罩層 -->
    <div
      v-if="isMobile && !collapsed"
      class="mobile-overlay"
      @click="collapsed = true"
    />
    <NLayout class="content-layout">
      <Navbar v-model:collapsed="collapsed" />
      <NLayoutContent class="content-wrapper">
        <div class="content-inner">
          <RouterView v-slot="{ Component }">
            <Transition name="fade" mode="out-in">
              <component :is="Component" :key="$route.fullPath" />
            </Transition>
          </RouterView>
        </div>
      </NLayoutContent>
    </NLayout>
  </NLayout>
</template>

<style scoped>
.main-layout {
  height: 100dvh;
  height: 100vh;
  overflow: hidden;
}

.content-layout {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  height: 100vh;
  overflow: hidden;
}

@supports (height: 100dvh) {
  .main-layout,
  .content-layout {
    height: 100dvh;
  }
}

.content-wrapper {
  flex: 1;
  overflow: auto;
  background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
  position: relative;
}

/* 添加微妙的背景紋理 */
.content-wrapper::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 50%, rgba(14, 165, 233, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
  pointer-events: none;
}

.content-inner {
  padding: 32px;
  max-width: 1600px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

@media (max-width: 1024px) {
  .content-inner {
    padding: 24px;
  }
}

@media (max-width: 640px) {
  .content-inner {
    padding: 16px;
  }
}

/* 優化過渡動畫 */
.fade-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 1, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}

/* 自訂滾動條 */
.content-wrapper::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.2);
}

/* 行動端遮罩層 */
.mobile-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 199;
  backdrop-filter: blur(2px);
}

@media (max-width: 768px) {
  :deep(.n-layout-sider) {
    position: absolute !important;
    z-index: 200;
    height: 100%;
  }
}
</style>
