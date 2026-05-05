<template>
  <router-view v-slot="{ Component, route }">
    <transition name="fade-slide" mode="out-in" appear>
      <KeepAlive :include="keepAliveRouteNames">
        <component
          :is="Component"
          v-if="appStore.reloadFlag"
          :key="appStore.aliveKeys[route.name] || route.fullPath"
        />
      </KeepAlive>
    </transition>
  </router-view>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store'
import { useRouter } from 'vue-router'
const appStore = useAppStore()
const router = useRouter()

const allRoutes = router.getRoutes()
const keepAliveRouteNames = computed(() => {
  return allRoutes.filter((route) => route.meta?.keepAlive).map((route) => route.name)
})
</script>
