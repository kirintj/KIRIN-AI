<script setup lang="ts">
defineProps<{ text?: string }>()
</script>

<template>
  <div class="hm-loading-dots">
    <span v-if="text" class="hm-loading-text">{{ text }}</span>
    <div class="hm-dots"><span></span><span></span><span></span></div>
  </div>
</template>

<style scoped>
.hm-loading-dots {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
}

.hm-dots {
  display: flex;
  gap: 4px;
}

.hm-dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--hm-brand);
  animation: hm-bounce 1.2s infinite cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-dots span:nth-child(2) { animation-delay: 0.15s; }
.hm-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes hm-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; box-shadow: none; }
  40% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 8px rgba(10, 89, 247, 0.4); }
}

.hm-loading-text {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}
</style>
