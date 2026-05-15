<script setup lang="ts">
import { useTrackerStore } from '@/store/modules/tracker'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NPopconfirm } from 'naive-ui'
import { useTrackerDrag } from '../composables/useTrackerDrag'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const store = useTrackerStore()

const emit = defineEmits<{
  edit: [app: any]
}>()

const {
  dragAppId,
  dragOverStatus,
  onCardDragStart,
  onCardDragEnd,
  onColDragOver,
  onColDragLeave,
  onColDrop,
} = useTrackerDrag(async (appId, status) => {
  await store.moveApplication(appId, status)
})

const handleDelete = async (appId: string) => {
  await store.deleteApplication(appId)
}

const handleMove = async (appId: string, newStatus: string) => {
  await store.moveApplication(appId, newStatus)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="hm-kanban">
    <div
      v-for="status in store.STATUS_LIST"
      :key="status"
      :class="['hm-kanban-col', { dragover: dragOverStatus === status }]"
      @dragover="onColDragOver($event, status)"
      @dragleave="onColDragLeave"
      @drop="onColDrop(status)"
    >
      <div class="hm-kanban-col-header">
        <span class="hm-kanban-dot" :style="{ background: store.STATUS_COLORS[status] }" />
        <span class="hm-kanban-col-title">{{ store.STATUS_LABELS[status] }}</span>
        <span class="hm-kanban-col-count">{{ store.getApplicationsByStatus(status).length }}</span>
      </div>
      <div class="hm-kanban-col-body">
        <div
          v-for="app in store.getApplicationsByStatus(status)"
          :key="app.id"
          :class="['hm-app-card', { dragging: dragAppId === app.id }]"
          draggable="true"
          @dragstart="onCardDragStart(app.id)"
          @dragend="onCardDragEnd"
        >
          <div class="hm-app-card-header">
            <span class="hm-app-company">{{ app.company }}</span>
            <div class="hm-app-card-menu" @click.stop>
              <NPopconfirm @positive-click="handleDelete(app.id)">
                <template #trigger>
                  <button class="hm-app-card-action">
                    <TheIcon icon="icon-park-outline:delete" :size="12" />
                  </button>
                </template>
                {{ t('views.tracker.confirm_delete') }}
              </NPopconfirm>
            </div>
          </div>
          <div class="hm-app-position">{{ app.position }}</div>
          <div v-if="app.salary" class="hm-app-salary">{{ app.salary }}</div>
          <div class="hm-app-meta">
            <span v-if="app.location">
              <TheIcon icon="icon-park-outline:position" :size="11" /> {{ app.location }}
            </span>
            <span v-if="app.source">
              <TheIcon icon="icon-park-outline:link" :size="11" /> {{ app.source }}
            </span>
            <span>{{ formatDate(app.created_at) }}</span>
          </div>
          <div class="hm-app-move">
            <select
              class="hm-move-select"
              :value="app.status"
              @change="handleMove(app.id, ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="s in store.STATUS_LIST" :key="s" :value="s">
                {{ store.STATUS_LABELS[s] }}
              </option>
            </select>
            <button class="hm-app-edit-btn" @click="emit('edit', app)">
              <TheIcon icon="icon-park-outline:edit" :size="12" />
              {{ t('views.tracker.btn_edit') }}
            </button>
          </div>
        </div>
        <div v-if="store.getApplicationsByStatus(status).length === 0" class="hm-kanban-empty">
          {{ t('views.tracker.empty_no_records') }}
        </div>
      </div>
    </div>
  </div>
</template>
