<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NInput, NSelect } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useJobQuery } from '../composables/useJobQuery'
import { useMarkdown } from '@/composables/useMarkdown'
import FormResultWrapper from './FormResultWrapper.vue'

const { t } = useI18n()
const { formatMarkdown } = useMarkdown()

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { loading, result, execute } = useJobQuery(job.jobGuide, 'guide')

const guideScenario = ref('')
const guideGoal = ref('成功求职')

const scenarioOptions = computed(() => [
  { label: t('views.job_assistant.scenario_fresh'), value: '应届生求职' },
  { label: t('views.job_assistant.scenario_career_change'), value: '跨行业跳槽' },
  { label: t('views.job_assistant.scenario_tech_to_mgmt'), value: '技术转管理' },
  { label: t('views.job_assistant.scenario_big_company'), value: '大厂面试' },
  { label: t('views.job_assistant.scenario_promotion'), value: '职场晋升' },
  { label: t('views.job_assistant.scenario_switch'), value: '转行求职' },
  { label: t('views.job_assistant.scenario_returnee'), value: '海归求职' },
  { label: t('views.job_assistant.scenario_35plus'), value: '35+求职' },
])

const runGuide = () => {
  if (!guideScenario.value.trim()) {
    window.$message?.error(t('views.job_assistant.msg_select_scenario'))
    return
  }
  execute({ scenario: guideScenario.value, goal: guideGoal.value }, t('views.job_assistant.msg_guide_failed'))
}
</script>

<template>
  <div class="hm-guide">
    <FormResultWrapper
      :loading="loading"
      :has-result="!!result"
      :result-title="t('views.job_assistant.result_guide')"
      result-icon="icon-park-outline:map-draw"
      :skeleton-lines="8"
      @back="result = ''"
    >
      <template #form>
        <div class="hm-form-card">
          <div class="hm-form-row">
            <div class="hm-form-item">
              <label class="hm-form-label">{{ t('views.job_assistant.guide_scenario') }}</label>
              <NSelect
                v-model:value="guideScenario"
                :options="scenarioOptions"
                :placeholder="t('views.job_assistant.guide_scenario_placeholder')"
                filterable
                tag
              />
            </div>
            <div class="hm-form-item">
              <label class="hm-form-label">{{ t('views.job_assistant.guide_target') }}</label>
              <NInput v-model:value="guideGoal" :placeholder="t('views.job_assistant.guide_target_placeholder')" />
            </div>
          </div>
          <div class="hm-form-row hm-form-row-submit">
            <div class="hm-form-item hm-form-action">
              <button
                class="hm-submit-btn"
                :disabled="!guideScenario.trim() || loading"
                @click="runGuide"
              >
                <TheIcon v-if="loading" icon="icon-park-outline:loading" :size="16" color="#fff" class="hm-spin" />
                <TheIcon v-else icon="icon-park-outline:map-draw" :size="16" color="#fff" />
                {{ loading ? t('views.job_assistant.btn_generating') : t('views.job_assistant.btn_generate_guide') }}
              </button>
            </div>
          </div>
        </div>
      </template>

      <template #result>
        <div class="hm-markdown" v-html="formatMarkdown(result || '')"></div>
      </template>

      <template #result-footer>
        <span class="hm-ai-feedback-label">{{ t('views.job_assistant.feedback_guide') }}</span>
        <button class="hm-ai-feedback-btn" @click="emit('feedback', t('views.job_assistant.tab_guide'), result || '')">
          <TheIcon icon="icon-park-outline:like" :size="14" />
          {{ t('views.job_assistant.btn_feedback') }}
        </button>
      </template>
    </FormResultWrapper>
  </div>
</template>

<style scoped lang="scss">
@import '../styles/common.scss';

.hm-guide {
  width: 100%;
}
</style>
