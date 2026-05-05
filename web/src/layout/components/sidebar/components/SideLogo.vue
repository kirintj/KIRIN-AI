<template>
  <router-link h-56 f-c-c to="/">
    <div class="logo-icon">
      <icon-custom-logo text-32></icon-custom-logo>
    </div>
    <h2
      v-show="!appStore.collapsed"
      class="logo-text"
    >
      {{ title }}
    </h2>
  </router-link>
</template>

<script setup>
import { useAppStore } from '@/store'
const title = import.meta.env.VITE_TITLE
const appStore = useAppStore()
</script>

<style scoped>
.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--hm-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-text {
  margin-left: 10px;
  margin-right: 8px;
  max-width: 140px;
  flex-shrink: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--hm-font-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
