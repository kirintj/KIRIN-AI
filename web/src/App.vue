<template>
    <AppProvider>
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </AppProvider>
</template>

<script setup>
import AppProvider from '@/components/common/AppProvider.vue'

const themeOverrides = {
  Button: {
    borderRadiusSmall: '8px',
    borderRadiusMedium: '8px',
    borderRadiusLarge: '8px'
  }
}
</script>
