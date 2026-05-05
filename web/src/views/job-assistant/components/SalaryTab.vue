<script setup lang="ts">
import { ref } from 'vue'
import { NInput } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useJobQuery } from '../composables/useJobQuery'
import LoadingDots from './LoadingDots.vue'
import ResultCard from './ResultCard.vue'
import EmptyState from './EmptyState.vue'

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { loading, result, execute } = useJobQuery(job.jobSalary, 'salary_advice')

const salaryCity = ref('')
const salaryIndustry = ref('')
const salaryPosition = ref('')
const salaryExperience = ref('')
const salaryExpected = ref('')

const runSalary = () => {
  if (!salaryCity.value.trim() || !salaryPosition.value.trim()) {
    window.$message?.error('请输入城市和岗位')
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
    '薪资建议生成失败',
  )
}
</script>

<template>
  <div class="hm-salary">
    <div class="hm-form-card">
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">城市</label>
          <NInput v-model:value="salaryCity" placeholder="如：北京、上海..." />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">行业</label>
          <NInput v-model:value="salaryIndustry" placeholder="如：互联网、金融..." />
        </div>
      </div>
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">岗位</label>
          <NInput v-model:value="salaryPosition" placeholder="如：前端开发、数据分析师..." />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">工作年限</label>
          <NInput v-model:value="salaryExperience" placeholder="如：3年、5年..." />
        </div>
      </div>
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">期望薪资</label>
          <NInput v-model:value="salaryExpected" placeholder="如：25K-35K，留空为面议" />
        </div>
        <div class="hm-form-item hm-form-action">
          <button
            class="hm-submit-btn"
            :disabled="!salaryCity.trim() || !salaryPosition.trim() || loading"
            @click="runSalary"
          >
            <TheIcon v-if="loading" icon="icon-park-outline:loading" :size="16" color="#fff" class="hm-spin" />
            <TheIcon v-else icon="icon-park-outline:finance" :size="16" color="#fff" />
            {{ loading ? '生成中...' : '生成谈判建议' }}
          </button>
        </div>
      </div>
    </div>

    <LoadingDots v-if="loading" text="正在检索薪资报告文档..." />

    <ResultCard
      v-if="result && !loading"
      title="薪资谈判方案"
      :content="result"
      feedback-label="对薪资建议满意吗？"
      @feedback="emit('feedback', $event)"
    />

    <EmptyState
      v-if="!result && !loading"
      icon="icon-park-outline:finance"
      text="输入城市和岗位，AI 将检索薪资报告生成谈判话术"
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
