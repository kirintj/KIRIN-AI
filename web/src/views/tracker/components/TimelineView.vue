<script setup lang="ts">
import { useTrackerStore } from '@/store/modules/tracker'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NPopconfirm } from 'naive-ui'

const store = useTrackerStore()

const emit = defineEmits<{
  edit: [app: any]
  add: []
}>()

const handleDelete = async (appId: string) => {
  await store.deleteApplication(appId)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="hm-timeline-view">
    <div v-if="store.timelineApplications.length === 0" class="hm-list-empty">
      <TheIcon icon="icon-park-outline:time" :size="48" color="var(--hm-font-fourth)" />
      <p>暂无求职记录</p>
      <span @click="emit('add')">添加第一条记录</span>
    </div>
    <div v-else class="hm-timeline-list">
      <div
        v-for="app in store.timelineApplications"
        :key="app.id"
        class="hm-timeline-item"
      >
        <div class="hm-timeline-dot" :style="{ background: store.STATUS_COLORS[app.status] }" />
        <div class="hm-timeline-line" />
        <div class="hm-timeline-card">
          <div class="hm-timeline-card-header">
            <span class="hm-timeline-company">{{ app.company }}</span>
            <span
              class="hm-timeline-status"
              :style="{ background: store.STATUS_COLORS[app.status] + '14', color: store.STATUS_COLORS[app.status] }"
            >
              {{ store.STATUS_LABELS[app.status] }}
            </span>
          </div>
          <div class="hm-timeline-position">{{ app.position }}</div>
          <div class="hm-timeline-meta">
            <span v-if="app.salary">{{ app.salary }}</span>
            <span v-if="app.location">{{ app.location }}</span>
            <span>{{ formatDate(app.created_at) }}</span>
          </div>
          <div class="hm-timeline-actions">
            <button class="hm-timeline-btn" @click="emit('edit', app)">编辑</button>
            <NPopconfirm @positive-click="handleDelete(app.id)">
              <template #trigger>
                <button class="hm-timeline-btn danger">删除</button>
              </template>
              确定删除？
            </NPopconfirm>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
