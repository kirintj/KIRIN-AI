<template>
  <n-layout has-sider wh-full>
    <template v-if="isMobile">
      <n-drawer
        v-model:show="mobileDrawerVisible"
        :width="260"
        placement="left"
        :auto-focus="false"
        class="hm-mobile-drawer"
      >
        <n-drawer-content :native-scrollbar="false" body-content-style="padding: 0;">
          <SideBar />
        </n-drawer-content>
      </n-drawer>
    </template>
    <template v-else>
      <n-layout-sider
        collapse-mode="width"
        :collapsed-width="64"
        :width="220"
        :native-scrollbar="false"
        :collapsed="appStore.collapsed"
        class="hm-sider"
      >
        <SideBar />
      </n-layout-sider>
    </template>

    <article flex-col flex-1 overflow-hidden>
      <header
        class="hm-header"
        :style="`height: ${headerHeight}px`"
      >
        <AppHeader :is-mobile="isMobile" @toggle-drawer="mobileDrawerVisible = !mobileDrawerVisible" />
      </header>
      <section v-if="showTags && !isMobile" class="hm-tags-bar">
        <TagsBar />
      </section>
      <section flex-1 overflow-hidden class="hm-main">
        <AppMain />
      </section>
    </article>
  </n-layout>
</template>

<script setup>
import AppHeader from './components/header/index.vue'
import SideBar from './components/sidebar/index.vue'
import AppMain from './components/AppMain.vue'
import TagsBar from './components/tags/index.vue'
import { useAppStore } from '@/store'
import { header, tags } from '~/settings'
import { useBreakpoints } from '@vueuse/core'

const appStore = useAppStore()
const breakpointsEnum = {
  xl: 1600,
  lg: 1199,
  md: 991,
  sm: 666,
  xs: 575,
}
const breakpoints = reactive(useBreakpoints(breakpointsEnum))
const isMobile = breakpoints.smaller('sm')
const isPad = breakpoints.between('sm', 'md')
const isPC = breakpoints.greater('md')

const mobileDrawerVisible = ref(false)
const showTags = ref(tags?.show ?? false)

const headerHeight = computed(() => {
  if (isMobile.value) return 48
  return header.height
})

watchEffect(() => {
  if (isMobile.value) {
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }
  if (isPad.value) {
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }
  if (isPC.value) {
    appStore.setCollapsed(false)
    appStore.setFullScreen(true)
  }
})

watch(isMobile, (val) => {
  if (val) mobileDrawerVisible.value = false
})

const route = useRoute()
watch(() => route.path, () => {
  if (isMobile.value) mobileDrawerVisible.value = false
})
</script>

<style scoped>
.hm-sider {
  background: var(--hm-bg-secondary) !important;
  border-right: 1px solid var(--hm-divider);
}

.hm-header {
  display: flex;
  align-items: center;
  background: var(--hm-bg-secondary);
  padding: 0 20px;
  border-bottom: 1px solid var(--hm-divider);
}

@media (max-width: 768px) {
  .hm-header {
    padding: 0 12px;
  }
}

.hm-tags-bar {
  flex-shrink: 0;
}

.hm-main {
  background: var(--hm-bg-primary);
}
</style>

<style>
.hm-mobile-drawer .n-drawer-body-content-wrapper {
  padding: 0 !important;
}
</style>
