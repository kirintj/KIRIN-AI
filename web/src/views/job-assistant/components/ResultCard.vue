<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useMarkdown } from '@/composables/useMarkdown'

const { t } = useI18n()

const props = defineProps<{
  title: string
  content: string
  feedbackLabel?: string
}>()

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()
const { formatMarkdown } = useMarkdown()
</script>

<template>
  <div class="hm-result-card">
    <div class="hm-result-header">
      <h3 class="hm-result-title">{{ title }}</h3>
    </div>
    <div class="hm-markdown" v-html="formatMarkdown(content)"></div>
    <div class="hm-feedback-bar">
      <span class="hm-feedback-label">{{ feedbackLabel || t('views.job_assistant.result_satisfied') }}</span>
      <button class="hm-feedback-btn" @click="emit('feedback', title, content)">
        <TheIcon icon="icon-park-outline:like" :size="14" />
        {{ t('views.job_assistant.btn_feedback') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.hm-result-card {
  background: var(--hm-bg-secondary);
  border-radius: var(--hm-radius-lg);
  padding: 20px;
  box-shadow: var(--hm-shadow-sm);
}

.hm-result-header {
  margin-bottom: 16px;
}

.hm-result-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-markdown {
  font-size: 14px;
  line-height: 1.7;
  color: var(--hm-font-primary);
}

.hm-feedback-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--hm-divider);
  margin-top: 16px;
}

.hm-feedback-label {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}

.hm-feedback-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-secondary);
  font-size: 12px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.hm-feedback-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}
</style>
