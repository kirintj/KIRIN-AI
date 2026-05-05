<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'

defineProps<{ icon: string; text: string }>()
</script>

<template>
  <div class="hm-empty">
    <TheIcon :icon="icon" :size="48" color="var(--hm-font-fourth)" />
    <p>{{ text }}</p>
  </div>
</template>

<style scoped>
.hm-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.hm-empty p {
  font-size: 14px;
  color: var(--hm-font-tertiary);
  margin-top: 12px;
}
</style>
