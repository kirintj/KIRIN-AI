<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NInput, NUpload, NSteps, NStep, NTag, NProgress,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useFileUpload } from '@/composables/useFileUpload'
import { useMarkdown } from '@/composables/useMarkdown'
import LoadingDots from './LoadingDots.vue'
import EmptyState from './EmptyState.vue'

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { formatMarkdown } = useMarkdown()

const resumeText = ref('')
const jdText = ref('')
const currentStep = ref(0)
const loading = ref(false)
const pipelineRunning = ref(false)
const useRagOptimize = ref(true)

const resumeData = ref<any>(null)
const jdData = ref<any>(null)
const matchData = ref<any>(null)
const optimizedResume = ref('')
const planData = ref('')
const ragSources = ref<string[]>([])

const matchScore = computed(() => matchData.value?.score || 0)
const matchScoreColor = computed(() => {
  const s = matchScore.value
  if (s >= 80) return '#64BB5C'
  if (s >= 60) return '#ED6F21'
  return '#E84026'
})

const resumeFileList = ref<any[]>([])
const jdFileList = ref<any[]>([])
const { uploading: resumeUploading, parseFile: parseResumeFile } = useFileUpload()
const { uploading: jdUploading, parseFile: parseJdFile } = useFileUpload()

const handleResumeUpload = async ({ file, onFinish, onError }: any) => {
  const nativeFile = file.file || file
  if (!nativeFile) { onError(); return }
  const result = await parseResumeFile(nativeFile)
  if (result?.text) {
    resumeText.value = result.text.trim()
    resumeFileList.value = []
    onFinish()
  } else { onError() }
}

const handleJdUpload = async ({ file, onFinish, onError }: any) => {
  const nativeFile = file.file || file
  if (!nativeFile) { onError(); return }
  const result = await parseJdFile(nativeFile)
  if (result?.text) {
    jdText.value = result.text.trim()
    jdFileList.value = []
    onFinish()
  } else { onError() }
}

const resetAll = () => {
  currentStep.value = 0
  resumeData.value = null
  jdData.value = null
  matchData.value = null
  optimizedResume.value = ''
  planData.value = ''
  ragSources.value = []
}

const runPipeline = async () => {
  if (!resumeText.value.trim() || !jdText.value.trim()) {
    window.$message?.error('请输入简历和岗位描述')
    return
  }

  pipelineRunning.value = true
  resetAll()

  try {
    currentStep.value = 1
    loading.value = true
    const resumeRes = await job.jobParseResume({ resume_text: resumeText.value })
    resumeData.value = resumeRes.data

    currentStep.value = 2
    const jdRes = await job.jobParseJD({ jd_text: jdText.value })
    jdData.value = jdRes.data

    currentStep.value = 3
    const matchRes = await job.jobMatch({
      resume_json: JSON.stringify(resumeData.value),
      jd_json: JSON.stringify(jdData.value),
    })
    matchData.value = matchRes.data

    currentStep.value = 4
    if (useRagOptimize.value) {
      const optimizeRes = await job.jobOptimizeRag({
        resume_text: resumeText.value,
        jd_text: jdText.value,
        match_result: JSON.stringify(matchData.value),
      })
      optimizedResume.value = optimizeRes.data?.optimized_resume || ''
      ragSources.value = optimizeRes.data?.sources || []
    } else {
      const optimizeRes = await job.jobOptimize({
        resume_text: resumeText.value,
        jd_text: jdText.value,
        match_result: JSON.stringify(matchData.value),
      })
      optimizedResume.value = optimizeRes.data?.optimized_resume || ''
      ragSources.value = []
    }

    currentStep.value = 5
    const planRes = await job.jobPlan({
      resume_summary: JSON.stringify(resumeData.value),
      jd_text: jdText.value,
      match_result: JSON.stringify(matchData.value),
    })
    planData.value = planRes.data?.plan || ''

    currentStep.value = 6
    window.$message?.success('求职分析完成！')
  } catch (error: any) {
    window.$message?.error(error?.message || '分析失败，请重试')
  } finally {
    loading.value = false
    pipelineRunning.value = false
  }
}

defineExpose({ resumeText, jdText, pipelineRunning, runPipeline })
</script>

<template>
  <div class="hm-pipeline">
    <div class="hm-input-grid">
      <div class="hm-input-block">
        <div class="hm-input-block-header">
          <div class="hm-input-block-icon" style="background: rgba(10,89,247,0.08)">
            <TheIcon icon="icon-park-outline:clipboard" :size="18" color="#0A59F7" />
          </div>
          <span class="hm-input-block-title">上传简历</span>
          <NUpload
            v-model:file-list="resumeFileList"
            :custom-request="handleResumeUpload"
            :max="1"
            :show-file-list="false"
            :disabled="pipelineRunning || resumeUploading"
          >
            <button class="hm-upload-chip" :disabled="pipelineRunning || resumeUploading">
              <TheIcon icon="material-symbols:upload" :size="14" />
              {{ resumeUploading ? '解析中...' : '上传文件' }}
            </button>
          </NUpload>
        </div>
        <NInput
          v-model:value="resumeText"
          type="textarea"
          placeholder="粘贴你的简历内容（支持 Markdown 格式）..."
          :rows="8"
          :disabled="pipelineRunning"
          class="hm-textarea"
        />
        <p class="hm-input-hint">支持 PDF/DOCX/TXT/MD，文件仅解析文本，不入库</p>
      </div>

      <div class="hm-input-block">
        <div class="hm-input-block-header">
          <div class="hm-input-block-icon" style="background: rgba(114,46,209,0.08)">
            <TheIcon icon="icon-park-outline:doc-search" :size="18" color="#722ED1" />
          </div>
          <span class="hm-input-block-title">岗位描述</span>
          <NUpload
            v-model:file-list="jdFileList"
            :custom-request="handleJdUpload"
            :max="1"
            :show-file-list="false"
            :disabled="pipelineRunning || jdUploading"
          >
            <button class="hm-upload-chip" :disabled="pipelineRunning || jdUploading">
              <TheIcon icon="material-symbols:upload" :size="14" />
              {{ jdUploading ? '解析中...' : '上传文件' }}
            </button>
          </NUpload>
        </div>
        <NInput
          v-model:value="jdText"
          type="textarea"
          placeholder="粘贴目标岗位的 JD（职位描述）..."
          :rows="8"
          :disabled="pipelineRunning"
          class="hm-textarea"
        />
        <p class="hm-input-hint">支持 PDF/DOCX/TXT/MD，文件仅解析文本，不入库</p>
      </div>
    </div>

    <div class="hm-rag-toggle">
      <button
        :class="['hm-toggle-chip', { active: useRagOptimize }]"
        @click="useRagOptimize = !useRagOptimize"
      >
        <TheIcon :icon="useRagOptimize ? 'icon-park-outline:link-two' : 'icon-park-outline:balance'" :size="14" />
        {{ useRagOptimize ? 'RAG 增强优化' : '普通优化' }}
      </button>
    </div>

    <div v-if="pipelineRunning || currentStep > 0" class="hm-progress-section">
      <NSteps :current="currentStep" :status="pipelineRunning ? 'process' : 'finish'" size="small">
        <NStep title="简历解析" />
        <NStep title="JD 分析" />
        <NStep title="匹配度" />
        <NStep :title="useRagOptimize ? 'RAG优化' : '优化'" />
        <NStep title="投递计划" />
        <NStep title="完成" />
      </NSteps>
    </div>

    <LoadingDots v-if="loading" text="AI 正在分析中，请稍候..." />

    <div v-if="currentStep >= 3 && !loading" class="hm-results">
      <div class="hm-result-card">
        <div class="hm-result-header">
          <h3 class="hm-result-title">匹配度分析</h3>
        </div>
        <div class="hm-match-area">
          <NProgress
            type="circle"
            :percentage="matchScore"
            :color="matchScoreColor"
            :rail-color="'var(--hm-border)'"
            :stroke-width="8"
            style="margin-right: 24px"
          >
            {{ matchScore }}%
          </NProgress>
          <div class="hm-match-details">
            <div v-if="matchData?.matched_skills?.length" class="hm-match-group">
              <div class="hm-match-label" style="color: #64BB5C">已满足技能</div>
              <div class="hm-tag-list">
                <NTag v-for="s in matchData.matched_skills" :key="s" size="small" round style="margin: 2px">{{ s }}</NTag>
              </div>
            </div>
            <div v-if="matchData?.missing_skills?.length" class="hm-match-group">
              <div class="hm-match-label" style="color: #E84026">缺失技能</div>
              <div class="hm-tag-list">
                <NTag v-for="s in matchData.missing_skills" :key="s" type="error" size="small" round style="margin: 2px">{{ s }}</NTag>
              </div>
            </div>
            <div v-if="matchData?.strengths?.length" class="hm-match-group">
              <div class="hm-match-label" style="color: #0A59F7">优势</div>
              <ul class="hm-detail-list"><li v-for="s in matchData.strengths" :key="s">{{ s }}</li></ul>
            </div>
            <div v-if="matchData?.weaknesses?.length" class="hm-match-group">
              <div class="hm-match-label" style="color: #ED6F21">不足</div>
              <ul class="hm-detail-list"><li v-for="s in matchData.weaknesses" :key="s">{{ s }}</li></ul>
            </div>
            <div v-if="matchData?.detail" class="hm-match-group">
              <div class="hm-match-label">综合分析</div>
              <p class="hm-detail-text">{{ matchData.detail }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="hm-result-card">
        <div class="hm-result-header">
          <h3 class="hm-result-title">优化后简历</h3>
          <div v-if="ragSources.length" class="hm-rag-sources">
            <TheIcon icon="icon-park-outline:link-two" :size="14" color="var(--hm-brand)" />
            <span>参考来源：{{ ragSources.join(', ') }}</span>
          </div>
        </div>
        <div class="hm-markdown" v-html="formatMarkdown(optimizedResume)"></div>
        <div v-if="optimizedResume" class="hm-feedback-bar">
          <span class="hm-feedback-label">对优化结果满意吗？</span>
          <button class="hm-feedback-btn" @click="emit('feedback', '简历优化', optimizedResume)">
            <TheIcon icon="icon-park-outline:like" :size="14" />
            评价反馈
          </button>
        </div>
      </div>

      <div v-if="planData" class="hm-result-card">
        <div class="hm-result-header">
          <h3 class="hm-result-title">投递计划</h3>
        </div>
        <div class="hm-markdown" v-html="formatMarkdown(planData)"></div>
      </div>
    </div>

    <EmptyState
      v-if="currentStep === 0 && !loading"
      icon="icon-park-outline:resume"
      text="输入简历和岗位描述，点击「一键分析」开始"
    />
  </div>
</template>

<style scoped lang="scss">
@import '../styles/common.scss';

.hm-pipeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.hm-input-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  width: 100%;
}

.hm-input-block {
  background: var(--hm-bg-secondary);
  border-radius: var(--hm-radius-lg);
  padding: 16px;
  box-shadow: var(--hm-shadow-sm);
  min-width: 0;
}

.hm-input-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.hm-input-block-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--hm-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hm-input-block-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
  width: 70px;
}

.hm-upload-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-container-secondary);
  font-size: 12px;
  color: var(--hm-font-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.hm-upload-chip:hover:not(:disabled) {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-upload-chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hm-input-hint {
  font-size: 12px;
  color: var(--hm-font-fourth);
  margin-top: 6px;
}

.hm-rag-toggle {
  display: flex;
  justify-content: center;
}

.hm-toggle-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-secondary);
  font-size: 13px;
  color: var(--hm-font-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.hm-toggle-chip:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-toggle-chip.active {
  background: var(--hm-brand-light);
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-progress-section {
  background: var(--hm-bg-secondary);
  border-radius: var(--hm-radius-lg);
  padding: 20px;
  box-shadow: var(--hm-shadow-sm);
}

.hm-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hm-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hm-rag-sources {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--hm-brand);
}

.hm-match-area {
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

.hm-match-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hm-match-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-match-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-primary);
}

.hm-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.hm-detail-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--hm-font-secondary);
  line-height: 1.8;
}

.hm-detail-text {
  font-size: 13px;
  color: var(--hm-font-secondary);
  line-height: 1.8;
  margin: 0;
}

@media (max-width: 768px) {
  .hm-input-grid { grid-template-columns: 1fr; }
  .hm-match-area { flex-direction: column; align-items: center; }
}
</style>
