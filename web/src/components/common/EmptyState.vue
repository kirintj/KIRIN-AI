<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'

defineProps<{
  icon?: string
  title?: string
  description?: string
}>()
</script>

<template>
  <div class="hm-empty-state">
    <div v-if="icon" class="hm-empty-icon">
      <TheIcon :icon="icon" :size="48" color="var(--hm-font-fourth)" />
    </div>
    <p v-if="title" class="hm-empty-title">{{ title }}</p>
    <p v-if="description" class="hm-empty-desc">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.hm-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
}

.hm-empty-icon {
  width: 80px;
  height: 80px;
  border-radius: var(--hm-radius-xl);
  background: var(--hm-bg-container-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.hm-empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
}

.hm-empty-desc {
  font-size: 13px;
  color: var(--hm-font-tertiary);
  max-width: 280px;
  line-height: 1.5;
}
</style>
