<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useTrackerStore } from '@/store/modules/tracker'
import { useTrackerForm } from './composables/useTrackerForm'
import TheIcon from '@/components/icon/TheIcon.vue'
import KanbanView from './components/KanbanView.vue'
import ListView from './components/ListView.vue'
import TimelineView from './components/TimelineView.vue'
import TrackerModal from './components/TrackerModal.vue'

const store = useTrackerStore()

const {
  showAddModal,
  showEditModal,
  editingApp,
  addForm,
  statusOptions,
  sourceOptions,
  handleAdd,
  openEdit,
  handleEdit,
} = useTrackerForm()

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

onMounted(async () => {
  await store.loadApplications()
  await store.loadStats()
})
</script>

<template>
  <div class="hm-tracker-layout">
    <div class="hm-sidebar">
      <div class="hm-sidebar-header">
        <span class="hm-sidebar-title">求职进度</span>
        <button class="hm-sidebar-new-btn" @click="showAddModal = true">
          <TheIcon icon="icon-park-outline:plus" :size="14" />
          添加
        </button>
      </div>

      <div v-if="store.stats" class="hm-tracker-stats-row">
        <div
          v-for="status in store.STATUS_LIST"
          :key="status"
          class="hm-tracker-stat-chip"
          :style="{ borderColor: store.STATUS_COLORS[status] + '40' }"
        >
          <span class="hm-tracker-stat-dot" :style="{ background: store.STATUS_COLORS[status] }" />
          <span class="hm-tracker-stat-label">{{ store.STATUS_LABELS[status] }}</span>
          <span class="hm-tracker-stat-count">{{ store.stats.by_status[status] || 0 }}</span>
        </div>
        <div class="hm-tracker-stat-chip total">
          <span class="hm-tracker-stat-label">合计</span>
          <span class="hm-tracker-stat-count">{{ store.stats.total }}</span>
        </div>
      </div>

      <div v-if="statusChartData.length" class="hm-tracker-chart-bar">
        <div
          v-for="item in statusChartData"
          :key="item.label"
          class="hm-tracker-chart-item"
        >
          <div class="hm-tracker-chart-label">{{ item.label }}</div>
          <div class="hm-tracker-chart-track">
            <div
              class="hm-tracker-chart-fill"
              :style="{ width: (item.value / maxChartValue * 100) + '%', background: item.color }"
            />
          </div>
          <div class="hm-tracker-chart-val" :style="{ color: item.color }">{{ item.value }}</div>
        </div>
      </div>
    </div>

    <div class="hm-tracker-main">
      <div class="hm-toolbar">
        <div class="hm-toolbar-left">
          <div class="hm-search-box">
            <TheIcon icon="icon-park-outline:search" :size="14" color="var(--hm-font-fourth)" />
            <input
              v-model="store.searchKeyword"
              class="hm-search-input"
              placeholder="搜索公司/职位..."
            />
          </div>
        </div>
        <div class="hm-toolbar-right">
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
        </div>
      </div>

      <div class="hm-tracker-content">
        <KanbanView
          v-if="store.viewMode === 'kanban'"
          @edit="openEdit"
        />
        <TimelineView
          v-else-if="store.viewMode === 'timeline'"
          @edit="openEdit"
          @add="showAddModal = true"
        />
        <ListView
          v-else
          @edit="openEdit"
          @add="showAddModal = true"
        />
      </div>
    </div>

    <TrackerModal
      :show="showAddModal"
      mode="add"
      :form-data="addForm"
      :status-options="statusOptions"
      :source-options="sourceOptions"
      @update:show="showAddModal = $event"
      @submit="handleAdd"
    />
    <TrackerModal
      :show="showEditModal"
      mode="edit"
      :form-data="editingApp"
      :status-options="statusOptions"
      :source-options="sourceOptions"
      @update:show="showEditModal = $event"
      @submit="handleEdit"
    />
  </div>
</template>

<style lang="scss">
@use './styles/tracker.scss';
</style>
