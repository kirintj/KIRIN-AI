<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'

const props = defineProps<{
  modelValue: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'send'): void
  (e: 'quick-send', text: string): void
}>()

const quickChips = [
  { label: '面试', text: '帮我准备面试' },
  { label: '薪资', text: '薪资谈判建议' },
  { label: '攻略', text: '求职攻略' },
  { label: '待办', text: '帮我创建一个待办' },
]

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('send')
  }
}
</script>

<template>
  <div class="hm-chat-input-area">
    <div class="hm-input-box">
      <textarea
        :value="modelValue"
        class="hm-textarea"
        placeholder="输入消息，Agent 自动识别意图..."
        rows="2"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @keydown="handleKeydown"
      />
      <div class="hm-input-actions">
        <div class="hm-input-chips">
          <button
            v-for="chip in quickChips"
            :key="chip.label"
            class="hm-mini-chip"
            @click="emit('quick-send', chip.text)"
          >
            {{ chip.label }}
          </button>
        </div>
        <button
          class="hm-send-btn"
          :class="{ active: modelValue.trim() && !isLoading }"
          :disabled="!modelValue.trim() || isLoading"
          @click="emit('send')"
        >
          <TheIcon icon="icon-park-outline:up-small" :size="18" color="var(--hm-font-on-brand)" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hm-chat-input-area {
  padding: 12px 16px 20px;
  flex-shrink: 0;
}

.hm-input-box {
  max-width: 720px;
  margin: 0 auto;
}

.hm-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hm-input-chips {
  display: flex;
  gap: 6px;
}

.hm-mini-chip {
  padding: 3px 10px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  font-size: 12px;
  color: var(--hm-font-tertiary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-mini-chip:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  background: var(--hm-brand-light);
  transform: translateY(-1px);
}
</style>
