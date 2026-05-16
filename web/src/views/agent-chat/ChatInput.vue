<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  modelValue: string
  isLoading: boolean
  useLlmRouter: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'send'): void
  (e: 'update:useLlmRouter', val: boolean): void
}>()

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
        :placeholder="t('views.agent_chat.input_placeholder')"
        rows="2"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @keydown="handleKeydown"
      />
      <div class="hm-input-actions">
        <button
          class="hm-router-chip"
          :class="{ active: useLlmRouter }"
          @click="emit('update:useLlmRouter', !useLlmRouter)"
        >
          <TheIcon icon="icon-park-outline:brain" :size="13" />
          {{ t('views.agent_chat.llm_router') }}
        </button>
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
  max-width: 70%;
  margin: 0 auto;
}

.hm-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hm-router-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--hm-radius-full);
  border: 1px solid var(--hm-border);
  background: transparent;
  font-size: 12px;
  color: var(--hm-font-fourth);
  cursor: pointer;
  transition: all 0.2s var(--hm-spring);
}

.hm-router-chip:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-router-chip.active {
  border-color: var(--hm-brand);
  background: var(--hm-brand-light);
  color: var(--hm-brand);
}

@media (max-width: 768px) {
  .hm-input-box {
    max-width: 100%;
  }
  .hm-chat-input-area {
    padding: 8px 12px 12px;
  }
}
</style>
