<script setup lang="ts">
import { onMounted } from 'vue'
import { useTrackerStore } from '@/store/modules/tracker'
import { useTrackerForm } from './composables/useTrackerForm'
import TrackerHeader from './components/TrackerHeader.vue'
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

onMounted(async () => {
  await store.loadApplications()
  await store.loadStats()
})
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-tracker">
      <TrackerHeader @add="showAddModal = true" />

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
  </AppPage>
</template>

<style lang="scss">
@use './styles/tracker.scss';
</style>
