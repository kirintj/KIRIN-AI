<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NSelect } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useJobQuery } from '../composables/useJobQuery'
import LoadingDots from './LoadingDots.vue'
import ResultCard from './ResultCard.vue'
import EmptyState from './EmptyState.vue'

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { loading, result, execute } = useJobQuery(job.jobInterview, 'interview')

const interviewCompany = ref('')
const interviewPosition = ref('')
const interviewType = ref('综合面试')

const interviewTypeOptions = [
  { label: '综合面试', value: '综合面试' },
  { label: '技术面试', value: '技术面试' },
  { label: 'HR面试', value: 'HR面试' },
  { label: '行为面试', value: '行为面试' },
  { label: '群面', value: '群面' },
]

const runInterview = () => {
  if (!interviewCompany.value.trim() || !interviewPosition.value.trim()) {
    window.$message?.error('请输入企业和岗位')
    return
  }
  execute(
    { company: interviewCompany.value, position: interviewPosition.value, interview_type: interviewType.value },
    '面试问答生成失败',
  )
}
</script>

<template>
  <div class="hm-interview">
    <div class="hm-form-card">
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">目标企业</label>
          <NInput v-model:value="interviewCompany" placeholder="如：字节跳动、腾讯..." />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">目标岗位</label>
          <NInput v-model:value="interviewPosition" placeholder="如：前端开发、产品经理..." />
        </div>
      </div>
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">面试类型</label>
          <NSelect v-model:value="interviewType" :options="interviewTypeOptions" />
        </div>
        <div class="hm-form-item hm-form-action">
          <button
            class="hm-submit-btn"
            :disabled="!interviewCompany.trim() || !interviewPosition.trim() || loading"
            @click="runInterview"
          >
            <TheIcon v-if="loading" icon="icon-park-outline:loading" :size="16" color="#fff" class="hm-spin" />
            <TheIcon v-else icon="icon-park-outline:lightning" :size="16" color="#fff" />
            {{ loading ? '生成中...' : '生成面试准备' }}
          </button>
        </div>
      </div>
    </div>

    <LoadingDots v-if="loading" text="正在检索面试题库和企业文化文档..." />

    <ResultCard
      v-if="result && !loading"
      title="面试准备方案"
      :content="result"
      feedback-label="对面试方案满意吗？"
      @feedback="emit('feedback', $event)"
    />

    <EmptyState
      v-if="!result && !loading"
      icon="icon-park-outline:people-talk"
      text="输入企业和岗位，AI 将检索面试题库生成个性化应答"
    />
  </div>
</template>

<style scoped lang="scss">
@import '../styles/common.scss';

.hm-interview {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
