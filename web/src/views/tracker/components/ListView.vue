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
  <div class="hm-list-view">
    <div v-if="store.applications.length === 0" class="hm-list-empty">
      <TheIcon icon="icon-park-outline:sequence" :size="48" color="var(--hm-font-fourth)" />
      <p>暂无求职记录</p>
      <span @click="emit('add')">添加第一条记录</span>
    </div>
    <div v-else class="hm-list-table">
      <div class="hm-list-header">
        <span class="hm-list-col company">公司</span>
        <span class="hm-list-col position">职位</span>
        <span class="hm-list-col status">状态</span>
        <span class="hm-list-col salary">薪资</span>
        <span class="hm-list-col location">地点</span>
        <span class="hm-list-col source">渠道</span>
        <span class="hm-list-col date">日期</span>
        <span class="hm-list-col actions">操作</span>
      </div>
      <div
        v-for="app in store.applications"
        :key="app.id"
        class="hm-list-row"
      >
        <span class="hm-list-col company">{{ app.company }}</span>
        <span class="hm-list-col position">{{ app.position }}</span>
        <span class="hm-list-col status">
          <span
            class="hm-status-tag"
            :style="{ background: store.STATUS_COLORS[app.status] + '14', color: store.STATUS_COLORS[app.status] }"
          >
            {{ store.STATUS_LABELS[app.status] || app.status }}
          </span>
        </span>
        <span class="hm-list-col salary">{{ app.salary || '-' }}</span>
        <span class="hm-list-col location">{{ app.location || '-' }}</span>
        <span class="hm-list-col source">{{ app.source || '-' }}</span>
        <span class="hm-list-col date">{{ formatDate(app.created_at) }}</span>
        <span class="hm-list-col actions">
          <button class="hm-list-action" @click="emit('edit', app)">编辑</button>
          <NPopconfirm @positive-click="handleDelete(app.id)">
            <template #trigger>
              <button class="hm-list-action danger">删除</button>
            </template>
            确定删除？
          </NPopconfirm>
        </span>
      </div>
    </div>
  </div>
</template>
