<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NInput } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useJobQuery } from '../composables/useJobQuery'
import LoadingDots from '@/components/common/LoadingDots.vue'
import ResultCard from './ResultCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const { t } = useI18n()

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { loading, result, execute } = useJobQuery(job.jobSalary, 'salary_advice')

const salaryCity = ref('')
const salaryIndustry = ref('')
const salaryPosition = ref('')
const salaryExperience = ref('')
const salaryExpected = ref('')

const runSalary = () => {
  if (!salaryCity.value.trim() || !salaryPosition.value.trim()) {
    window.$message?.error(t('views.job_assistant.msg_enter_city_position'))
    return
  }
  execute(
    {
      city: salaryCity.value,
      industry: salaryIndustry.value,
      position: salaryPosition.value,
      experience: salaryExperience.value,
      expected_salary: salaryExpected.value || '面议',
    },
    t('views.job_assistant.msg_salary_failed'),
  )
}
</script>

<template>
  <div class="hm-salary">
    <div class="hm-form-card">
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.salary_city') }}</label>
          <NInput v-model:value="salaryCity" :placeholder="t('views.job_assistant.salary_city_placeholder')" />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.salary_industry') }}</label>
          <NInput v-model:value="salaryIndustry" :placeholder="t('views.job_assistant.salary_industry_placeholder')" />
        </div>
      </div>
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.salary_position') }}</label>
          <NInput v-model:value="salaryPosition" :placeholder="t('views.job_assistant.salary_position_placeholder')" />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.salary_experience') }}</label>
          <NInput v-model:value="salaryExperience" :placeholder="t('views.job_assistant.salary_experience_placeholder')" />
        </div>
      </div>
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">{{ t('views.job_assistant.salary_expected') }}</label>
          <NInput v-model:value="salaryExpected" :placeholder="t('views.job_assistant.salary_expected_placeholder')" />
        </div>
        <div class="hm-form-item hm-form-action">
          <button
            class="hm-submit-btn"
            :disabled="!salaryCity.trim() || !salaryPosition.trim() || loading"
            @click="runSalary"
          >
            <TheIcon v-if="loading" icon="icon-park-outline:loading" :size="16" color="#fff" class="hm-spin" />
            <TheIcon v-else icon="icon-park-outline:finance" :size="16" color="#fff" />
            {{ loading ? t('views.job_assistant.btn_generating') : t('views.job_assistant.btn_generate_salary') }}
          </button>
        </div>
      </div>
    </div>

    <LoadingDots v-if="loading" :text="t('views.job_assistant.loading_searching_salary')" />

    <ResultCard
      v-if="result && !loading"
      :title="t('views.job_assistant.result_salary')"
      :content="result"
      :feedback-label="t('views.job_assistant.feedback_salary')"
      @feedback="emit('feedback', $event)"
    />

    <EmptyState
      v-if="!result && !loading"
      icon="icon-park-outline:finance"
      :text="t('views.job_assistant.empty_salary')"
    />
  </div>
</template>

<style scoped lang="scss">
@import '../styles/common.scss';

.hm-salary {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
