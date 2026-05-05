<template>
  <n-layout has-sider wh-full>
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

    <article flex-col flex-1 overflow-hidden>
      <header
        class="hm-header"
        :style="`height: ${header.height}px`"
      >
        <AppHeader />
      </header>
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

.hm-main {
  background: var(--hm-bg-primary);
}
</style>
