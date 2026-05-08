<script setup lang="ts">
import { ref } from 'vue'
import { NInput, NSelect } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { job } from '@/api'
import { useJobQuery } from '../composables/useJobQuery'
import LoadingDots from '@/components/common/LoadingDots.vue'
import ResultCard from './ResultCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const emit = defineEmits<{ feedback: [query: string, answer: string] }>()

const { loading, result, execute } = useJobQuery(job.jobGuide, 'guide')

const guideScenario = ref('')
const guideGoal = ref('成功求职')

const scenarioOptions = [
  { label: '应届生求职', value: '应届生求职' },
  { label: '跨行业跳槽', value: '跨行业跳槽' },
  { label: '技术转管理', value: '技术转管理' },
  { label: '大厂面试', value: '大厂面试' },
  { label: '职场晋升', value: '职场晋升' },
  { label: '转行求职', value: '转行求职' },
  { label: '海归求职', value: '海归求职' },
  { label: '35+求职', value: '35+求职' },
]

const runGuide = () => {
  if (!guideScenario.value.trim()) {
    window.$message?.error('请选择或输入求职场景')
    return
  }
  execute({ scenario: guideScenario.value, goal: guideGoal.value }, '攻略生成失败')
}
</script>

<template>
  <div class="hm-guide">
    <div class="hm-form-card">
      <div class="hm-form-row">
        <div class="hm-form-item">
          <label class="hm-form-label">求职场景</label>
          <NSelect
            v-model:value="guideScenario"
            :options="scenarioOptions"
            placeholder="选择或输入场景"
            filterable
            tag
          />
        </div>
        <div class="hm-form-item">
          <label class="hm-form-label">目标</label>
          <NInput v-model:value="guideGoal" placeholder="如：成功求职、拿到大厂Offer..." />
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
            {{ loading ? '生成中...' : '生成攻略' }}
          </button>
        </div>
      </div>
    </div>

    <LoadingDots v-if="loading" text="正在检索求职攻略文档..." />

    <ResultCard
      v-if="result && !loading"
      title="求职攻略"
      :content="result"
      feedback-label="对攻略满意吗？"
      @feedback="emit('feedback', $event)"
    />

    <EmptyState
      v-if="!result && !loading"
      icon="icon-park-outline:map"
      text="选择求职场景，AI 将检索攻略文档生成步骤化行动指南"
    />
  </div>
</template>

<style scoped lang="scss">
@import '../styles/common.scss';

.hm-guide {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
