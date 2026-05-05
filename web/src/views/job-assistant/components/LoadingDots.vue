<script setup lang="ts">
defineProps<{ text?: string }>()
</script>

<template>
  <div class="hm-loading">
    <div class="hm-dots"><span></span><span></span><span></span></div>
    <span v-if="text" class="hm-loading-text">{{ text }}</span>
  </div>
</template>

<style scoped>
.hm-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 0;
}

.hm-dots {
  display: flex;
  gap: 4px;
}

.hm-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--hm-brand);
  animation: hm-bounce 1.2s infinite ease-in-out;
}

.hm-dots span:nth-child(2) { animation-delay: 0.15s; }
.hm-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes hm-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.hm-loading-text {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}
</style>
