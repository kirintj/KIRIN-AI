<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  loading: boolean
  hasResult: boolean
  resultTitle: string
  resultIcon: string
  iconBg?: string
  skeletonLines?: number
}>(), {
  iconBg: 'var(--hm-brand-bg-light)',
  skeletonLines: 6,
})

const emit = defineEmits<{ back: [] }>()
</script>

<template>
  <div class="hm-form-result-wrapper">
    <!-- Form state -->
    <Transition name="hm-form-result">
      <div v-if="!loading && !hasResult" key="form" class="hm-form-result-form">
        <slot name="form" />
      </div>
    </Transition>

    <!-- Loading state: skeleton -->
    <Transition name="hm-form-result">
      <div v-if="loading" key="skeleton" class="hm-ai-result-card">
        <div class="hm-ai-result-header">
          <div class="hm-ai-result-icon" :style="{ background: iconBg }">
            <TheIcon :icon="resultIcon" :size="18" color="var(--hm-brand)" />
          </div>
          <span class="hm-ai-result-title">{{ resultTitle }}</span>
        </div>
        <div class="hm-ai-result-body">
          <div class="hm-ai-skeleton">
            <div
              v-for="i in skeletonLines"
              :key="i"
              :class="['hm-skeleton-line', i % 3 === 0 ? 'short' : i % 2 === 0 ? 'medium' : 'full']"
            />
            <div class="hm-skeleton-tags">
              <div class="hm-skeleton-tag" />
              <div class="hm-skeleton-tag" />
              <div class="hm-skeleton-tag" />
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Result state -->
    <Transition name="hm-form-result">
      <div v-if="!loading && hasResult" key="result" class="hm-ai-result-card">
        <div class="hm-ai-result-header">
          <div class="hm-ai-result-icon" :style="{ background: iconBg }">
            <TheIcon :icon="resultIcon" :size="18" color="var(--hm-brand)" />
          </div>
          <span class="hm-ai-result-title">{{ resultTitle }}</span>
          <button class="hm-ai-back-btn" @click="emit('back')">
            <TheIcon icon="icon-park-outline:left" :size="14" />
            {{ t('views.job_assistant.btn_back_edit') }}
          </button>
        </div>
        <div class="hm-ai-result-body">
          <slot name="result" />
        </div>
        <div v-if="$slots['result-footer']" class="hm-ai-result-footer">
          <slot name="result-footer" />
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.hm-form-result-wrapper {
  position: relative;
  min-height: 200px;
}

.hm-form-result-form {
  animation: hm-fade-in-up 0.3s var(--hm-spring) both;
}
</style>
