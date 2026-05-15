<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NInput, NSelect } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useJobQuery } from '../composables/useJobQuery'
import LoadingDots from '@/components/common/LoadingDots.vue'
import ResultCard from './ResultCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const { t } = useI18n()

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { loading, result, execute } = useJobQuery(job.jobInterview, 'interview')

const interviewCompany = ref('')
const interviewPosition = ref('')
const interviewType = ref('综合面试')

const interviewTypeOptions = computed(() => [
  { label: t('views.job_assistant.type_comprehensive'), value: '综合面试' },
  { label: t('common.interview.type_tech'), value: '技术面试' },
  { label: t('common.interview.type_hr'), value: 'HR面试' },
  { label: t('common.interview.type_behavior'), value: '行为面试' },
  { label: t('views.job_assistant.type_group'), value: '群面' },
])

const runInterview = () => {
  if (!interviewCompany.value.trim() || !interviewPosition.value.trim()) {
    window.$message?.error(t('views.job_assistant.msg_enter_company_position'))
    return
  }
  execute(
    { company: interviewCompany.value, position: interviewPosition.value, interview_type: interviewType.value },
    t('views.job_assistant.msg_interview_failed'),
  )
}
</script>

<template>
  <div class="hm-interview">
    <div class="hm-form-card">
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.interview_company') }}</label>
          <NInput v-model:value="interviewCompany" :placeholder="t('views.job_assistant.interview_company_placeholder')" />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.interview_position') }}</label>
          <NInput v-model:value="interviewPosition" :placeholder="t('views.job_assistant.interview_position_placeholder')" />
        </div>
      </div>
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.interview_type') }}</label>
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
            {{ loading ? t('views.job_assistant.btn_generating') : t('views.job_assistant.btn_generate_interview') }}
          </button>
        </div>
      </div>
    </div>

    <LoadingDots v-if="loading" :text="t('views.job_assistant.loading_searching_interview')" />

    <ResultCard
      v-if="result && !loading"
      :title="t('views.job_assistant.result_interview')"
      :content="result"
      :feedback-label="t('views.job_assistant.feedback_interview')"
      @feedback="emit('feedback', $event)"
    />

    <EmptyState
      v-if="!result && !loading"
      icon="icon-park-outline:people-talk"
      :text="t('views.job_assistant.empty_interview')"
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
