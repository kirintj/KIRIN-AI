<script setup lang="ts">
import { computed } from 'vue'
import { useTrackerStore } from '@/store/modules/tracker'
import TheIcon from '@/components/icon/TheIcon.vue'

const store = useTrackerStore()

const emit = defineEmits<{
  add: []
}>()

const viewModes = [
  { key: 'kanban', label: '看板', icon: 'icon-park-outline:sequence' },
  { key: 'list', label: '列表', icon: 'icon-park-outline:list' },
  { key: 'timeline', label: '时间线', icon: 'icon-park-outline:time' },
]

const statusChartData = computed(() => {
  if (!store.stats) return []
  return store.STATUS_LIST.map((status) => ({
    label: store.STATUS_LABELS[status],
    value: store.stats.by_status[status] || 0,
    color: store.STATUS_COLORS[status],
  }))
})

const maxChartValue = computed(() => {
  return Math.max(...statusChartData.value.map((d) => d.value), 1)
})
</script>

<template>
  <div class="hm-tracker-header">
    <div class="hm-tracker-title-row">
      <h1 class="hm-tracker-title">求职进度追踪</h1>
      <div class="hm-tracker-actions">
        <div class="hm-search-box">
          <TheIcon icon="icon-park-outline:search" :size="14" color="var(--hm-font-fourth)" />
          <input
            v-model="store.searchKeyword"
            class="hm-search-input"
            placeholder="搜索公司/职位..."
          />
        </div>
        <div class="hm-view-toggle">
          <button
            v-for="mode in viewModes"
            :key="mode.key"
            :class="['hm-view-btn', { active: store.viewMode === mode.key }]"
            @click="store.viewMode = mode.key"
          >
            <TheIcon :icon="mode.icon" :size="14" />
            {{ mode.label }}
          </button>
        </div>
        <button class="hm-add-btn" @click="emit('add')">
          <TheIcon icon="icon-park-outline:plus" :size="16" />
          添加记录
        </button>
      </div>
    </div>

    <div v-if="store.stats" class="hm-stats-bar">
      <div
        v-for="status in store.STATUS_LIST"
        :key="status"
        class="hm-stat-chip"
        :style="{ borderColor: store.STATUS_COLORS[status] + '40' }"
      >
        <span class="hm-stat-dot" :style="{ background: store.STATUS_COLORS[status] }" />
        <span class="hm-stat-label">{{ store.STATUS_LABELS[status] }}</span>
        <span class="hm-stat-count">{{ store.stats.by_status[status] || 0 }}</span>
      </div>
      <div class="hm-stat-chip total">
        <span class="hm-stat-label">合计</span>
        <span class="hm-stat-count">{{ store.stats.total }}</span>
      </div>
    </div>

    <div v-if="statusChartData.length" class="hm-chart-bar">
      <div
        v-for="item in statusChartData"
        :key="item.label"
        class="hm-chart-item"
      >
        <div class="hm-chart-label">{{ item.label }}</div>
        <div class="hm-chart-track">
          <div
            class="hm-chart-fill"
            :style="{ width: (item.value / maxChartValue * 100) + '%', background: item.color }"
          />
        </div>
        <div class="hm-chart-val" :style="{ color: item.color }">{{ item.value }}</div>
      </div>
    </div>
  </div>
</template>
