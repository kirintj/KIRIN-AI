<template>
  <div class="hm-query-bar">
    <n-space wrap :size="[20, 12]">
      <slot />
      <div class="hm-query-actions">
        <button class="hm-query-btn reset" @click="emit('reset')">重置</button>
        <button class="hm-query-btn search" @click="emit('search')">搜索</button>
      </div>
    </n-space>
  </div>
</template>

<script setup>
const emit = defineEmits(['search', 'reset'])
</script>

<style scoped>
.hm-query-bar {
  min-height: 56px;
  display: flex;
  align-items: center;
  padding: 14px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  box-shadow: var(--hm-shadow-layered);
  margin-bottom: 20px;
}

.hm-query-actions {
  display: flex;
  gap: 8px;
  margin-left: 8px;
}

.hm-query-btn {
  padding: 6px 16px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-query-btn.reset {
  background: var(--hm-bg-secondary);
  color: var(--hm-font-primary);
}

.hm-query-btn.reset:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  transform: translateY(-1px);
}

.hm-query-btn.search {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: var(--hm-shadow-brand);
}

.hm-query-btn.search:hover {
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35);
  transform: translateY(-1px);
}
</style>
