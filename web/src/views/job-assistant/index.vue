<script setup lang="ts">
import { ref } from 'vue'
import { NButton, NTabs, NTabPane, NModal, NRate, NInput, NSpace } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import PipelineTab from './components/PipelineTab.vue'
import InterviewTab from './components/InterviewTab.vue'
import SalaryTab from './components/SalaryTab.vue'
import GuideTab from './components/GuideTab.vue'
import ResumeExportTab from './components/ResumeExportTab.vue'

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
    window.$message?.success('反馈已提交，感谢您的评价！')
    feedbackVisible.value = false
  } catch (error: any) {
    window.$message?.error('反馈提交失败')
  }
}

const handleQuickAnalysis = () => {
  activeTab.value = 'pipeline'
  pipelineRef.value?.runPipeline()
}

const tabs = [
  { name: 'pipeline', label: '简历优化', icon: 'icon-park-outline:clipboard' },
  { name: 'interview', label: '面试问答', icon: 'icon-park-outline:communication' },
  { name: 'salary', label: '薪资谈判', icon: 'icon-park-outline:finance' },
  { name: 'guide', label: '求职攻略', icon: 'icon-park-outline:map-draw' },
  { name: 'export', label: '简历导出', icon: 'icon-park-outline:export' },
]
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-job-page">
    <div class="hm-job-header">
      <div>
        <h1 class="hm-job-title">AI 求职助手</h1>
        <p class="hm-job-subtitle">简历优化 · 面试准备 · 薪资谈判 · 求职攻略</p>
      </div>
      <button
        class="hm-action-btn primary"
        :disabled="!pipelineRef?.resumeText?.trim() || !pipelineRef?.jdText?.trim()"
        @click="handleQuickAnalysis"
      >
        <TheIcon icon="icon-park-outline:rocket" :size="16" color="#fff" />
        一键分析
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

    <NModal v-model:show="feedbackVisible" preset="card" title="评价反馈" style="max-width: 480px; border-radius: var(--hm-radius-xl);">
      <div class="hm-feedback-form">
        <div class="hm-feedback-row">
          <label class="hm-feedback-label">评分</label>
          <NRate v-model:value="feedbackRating" />
        </div>
        <div class="hm-feedback-row">
          <label class="hm-feedback-label">修改意见</label>
          <NInput
            v-model:value="feedbackComment"
            type="textarea"
            placeholder="请输入您的建议或修改意见..."
            :rows="3"
          />
        </div>
      </div>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="feedbackVisible = false">取消</NButton>
          <NButton type="primary" @click="submitFeedback">提交反馈</NButton>
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
  box-shadow: var(--hm-shadow-layered), 0 8px 24px rgba(10, 89, 247, 0.06);
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

.hm-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-secondary);
  font-size: 14px;
  color: var(--hm-font-primary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-action-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(10, 89, 247, 0.12);
}

.hm-action-btn:active {
  transform: translateY(0) scale(0.97);
  transition-duration: 0.1s;
}

.hm-action-btn.primary {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: var(--hm-shadow-brand);
}

.hm-action-btn.primary:hover {
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35);
  transform: translateY(-2px);
}

.hm-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
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
  background: rgba(0, 0, 0, 0.02);
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
    padding: 20px 16px;
  }
  .hm-job-header {
    padding: 18px 20px;
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
</style>
