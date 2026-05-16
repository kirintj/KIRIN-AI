<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  modelValue: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void
  (e: 'send'): void
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
        <div></div>
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
</style>
