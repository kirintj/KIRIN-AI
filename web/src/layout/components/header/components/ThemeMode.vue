<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store'

const appStore = useAppStore()
const isDark = computed(() => appStore.isDark)
const toggleDark = () => {
  appStore.toggleDark()
}
</script>

<template>
  <n-icon mr-20 cursor-pointer size="18" @click="toggleDark">
    <icon-mdi-moon-waning-crescent v-if="isDark" />
    <icon-mdi-white-balance-sunny v-else />
  </n-icon>
</template>
