<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NTabs, NTabPane, NModal, NRate, NInput, NSpace } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import PipelineTab from './components/PipelineTab.vue'
import InterviewTab from './components/InterviewTab.vue'
import SalaryTab from './components/SalaryTab.vue'
import GuideTab from './components/GuideTab.vue'
import ResumeExportTab from './components/ResumeExportTab.vue'

const { t } = useI18n()

defineOptions({ name: '求职助手' })

const activeTab = ref('pipeline')
const pipelineRef = ref()

const feedbackVisible = ref(false)
const feedbackRating = ref(5)
const feedbackComment = ref('')
const feedbackRelatedQuery = ref('')
const feedbackRelatedAnswer = ref('')

const openFeedback = (query: string, answer: string) => {
  feedbackRelatedQuery.value = query
  feedbackRelatedAnswer.value = answer
  feedbackRating.value = 5
  feedbackComment.value = ''
  feedbackVisible.value = true
}

const submitFeedback = async () => {
  try {
    await job.jobFeedback({
      rating: feedbackRating.value,
      comment: feedbackComment.value,
      related_query: feedbackRelatedQuery.value,
      related_answer: feedbackRelatedAnswer.value,
    })
    window.$message?.success(t('views.job_assistant.msg_feedback_success'))
    feedbackVisible.value = false
  } catch (error: any) {
    window.$message?.error(t('views.job_assistant.msg_feedback_failed'))
  }
}

const handleQuickAnalysis = () => {
  activeTab.value = 'pipeline'
  pipelineRef.value?.runPipeline()
}

const tabs = computed(() => [
  { name: 'pipeline', label: t('views.job_assistant.tab_resume'), icon: 'icon-park-outline:clipboard' },
  { name: 'interview', label: t('views.job_assistant.tab_interview'), icon: 'icon-park-outline:communication' },
  { name: 'salary', label: t('views.job_assistant.tab_salary'), icon: 'icon-park-outline:finance' },
  { name: 'guide', label: t('views.job_assistant.tab_guide'), icon: 'icon-park-outline:map-draw' },
  { name: 'export', label: t('views.job_assistant.tab_export'), icon: 'icon-park-outline:export' },
])
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-job-page">
    <div class="hm-job-header">
      <div>
        <h1 class="hm-job-title">{{ t('views.job_assistant.page_title') }}</h1>
        <p class="hm-job-subtitle">{{ t('views.job_assistant.page_subtitle') }}</p>
      </div>
      <button
        class="hm-action-btn primary"
        :disabled="!pipelineRef?.resumeText?.trim() || !pipelineRef?.jdText?.trim()"
        @click="handleQuickAnalysis"
      >
        <TheIcon icon="icon-park-outline:rocket" :size="16" color="#fff" />
        {{ t('views.job_assistant.btn_quick_analysis') }}
      </button>
    </div>

    <div class="hm-tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        :class="['hm-tab-item', { active: activeTab === tab.name }]"
        @click="activeTab = tab.name"
      >
        <TheIcon :icon="tab.icon" :size="18" />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <div class="hm-tab-content">
      <PipelineTab v-show="activeTab === 'pipeline'" ref="pipelineRef" @feedback="openFeedback" />
      <InterviewTab v-show="activeTab === 'interview'" @feedback="openFeedback" />
      <SalaryTab v-show="activeTab === 'salary'" @feedback="openFeedback" />
      <GuideTab v-show="activeTab === 'guide'" @feedback="openFeedback" />
      <ResumeExportTab v-show="activeTab === 'export'" />
    </div>

    <NModal v-model:show="feedbackVisible" preset="card" :title="t('views.job_assistant.feedback_title')" style="max-width: 480px; border-radius: var(--hm-radius-xl);">
      <div class="hm-feedback-form">
        <div class="hm-feedback-row">
          <label class="hm-feedback-label">{{ t('views.job_assistant.feedback_score') }}</label>
          <NRate v-model:value="feedbackRating" />
        </div>
        <div class="hm-feedback-row">
          <label class="hm-feedback-label">{{ t('views.job_assistant.feedback_opinion') }}</label>
          <NInput
            v-model:value="feedbackComment"
            type="textarea"
            :placeholder="t('views.job_assistant.feedback_placeholder')"
            :rows="3"
          />
        </div>
      </div>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="feedbackVisible = false">{{ t('views.job_assistant.btn_cancel') }}</NButton>
          <NButton type="primary" @click="submitFeedback">{{ t('views.job_assistant.btn_submit_feedback') }}</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
  </AppPage>
</template>

<style scoped>
.hm-job-page {
  width: 100%;
  margin: 0 auto;
  padding: 32px 28px;
}

.hm-job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding: 24px 28px;
  border-radius: var(--hm-radius-xl);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass-strong);
  -webkit-backdrop-filter: var(--hm-blur-glass-strong);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered), 0 8px 24px var(--hm-brand-bg-light);
}

.hm-job-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
}

.hm-job-subtitle {
  font-size: 14px;
  color: var(--hm-font-tertiary);
}

.hm-tab-bar {
  display: flex;
  gap: 6px;
  padding: 4px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  margin-bottom: 24px;
}

.hm-tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--hm-radius-lg);
  background: transparent;
  font-size: 14px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-tab-item:hover {
  color: var(--hm-font-primary);
  background: var(--hm-hover-bg);
}

.hm-tab-item.active {
  background: var(--hm-bg-secondary);
  color: var(--hm-brand);
  font-weight: 500;
  box-shadow: var(--hm-shadow-layered);
}

.hm-tab-content {
  min-height: 400px;
  width: 100%;
}

.hm-feedback-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hm-feedback-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hm-feedback-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-primary);
}

@media (max-width: 768px) {
  .hm-job-page {
    padding: 16px 12px;
  }
  .hm-job-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 16px;
    gap: 12px;
  }
  .hm-job-title {
    font-size: 22px;
  }
  .hm-tab-item {
    padding: 8px 10px;
    font-size: 13px;
  }
  .hm-tab-item span {
    display: none;
  }
}

@media (max-width: 480px) {
  .hm-job-header {
    padding: 12px;
  }
}
</style>
