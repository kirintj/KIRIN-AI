<script setup lang="ts">
import { useTrackerStore } from '@/store/modules/tracker'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NPopconfirm } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { formatShortDate } from '@/utils/common/time'

const { t } = useI18n()
const store = useTrackerStore()

const emit = defineEmits<{
  edit: [app: any]
  add: []
}>()

const handleDelete = async (appId: string) => {
  await store.deleteApplication(appId)
}
</script>

<template>
  <div class="hm-list-view">
    <div v-if="store.applications.length === 0" class="hm-list-empty">
      <TheIcon icon="icon-park-outline:sequence" :size="48" color="var(--hm-font-fourth)" />
      <p>{{ t('views.tracker.empty_no_applications') }}</p>
      <span @click="emit('add')">{{ t('views.tracker.btn_add_first') }}</span>
    </div>
    <div v-else class="hm-list-table">
      <div class="hm-list-header">
        <span class="hm-list-col company">{{ t('views.tracker.col_company') }}</span>
        <span class="hm-list-col position">{{ t('views.tracker.col_position') }}</span>
        <span class="hm-list-col status">{{ t('views.tracker.col_status') }}</span>
        <span class="hm-list-col salary">{{ t('views.tracker.col_salary') }}</span>
        <span class="hm-list-col location">{{ t('views.tracker.col_location') }}</span>
        <span class="hm-list-col source">{{ t('views.tracker.col_source') }}</span>
        <span class="hm-list-col date">{{ t('views.tracker.col_date') }}</span>
        <span class="hm-list-col actions">{{ t('views.tracker.col_actions') }}</span>
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
        <span class="hm-list-col date">{{ formatShortDate(app.created_at) }}</span>
        <span class="hm-list-col actions">
          <button class="hm-list-action" @click="emit('edit', app)">{{ t('views.tracker.btn_edit') }}</button>
          <NPopconfirm @positive-click="handleDelete(app.id)">
            <template #trigger>
              <button class="hm-list-action danger">{{ t('views.tracker.btn_delete') }}</button>
            </template>
            {{ t('views.tracker.confirm_delete_short') }}
          </NPopconfirm>
        </span>
      </div>
    </div>
  </div>
</template>
