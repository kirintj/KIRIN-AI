<script setup lang="ts">
import { useTrackerStore } from '@/store/modules/tracker'
import { onMounted, ref, computed } from 'vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NModal, NForm, NFormItem, NInput, NSelect, NPopconfirm } from 'naive-ui'

const store = useTrackerStore()

const showAddModal = ref(false)
const showEditModal = ref(false)
const editingApp = ref<any>(null)
const dragAppId = ref<string | null>(null)
const dragOverStatus = ref<string | null>(null)

const addForm = ref({
  company: '',
  position: '',
  status: 'applied',
  salary: '',
  location: '',
  source: '',
  notes: '',
  contact: '',
})

const statusOptions = computed(() =>
  store.STATUS_LIST.map((s) => ({ label: store.STATUS_LABELS[s], value: s }))
)

const sourceOptions = [
  { label: 'Boss直聘', value: 'Boss直聘' },
  { label: '拉勾', value: '拉勾' },
  { label: '猎聘', value: '猎聘' },
  { label: '智联招聘', value: '智联招聘' },
  { label: '内推', value: '内推' },
  { label: '官网', value: '官网' },
  { label: '其他', value: '其他' },
]

const resetAddForm = () => {
  addForm.value = {
    company: '',
    position: '',
    status: 'applied',
    salary: '',
    location: '',
    source: '',
    notes: '',
    contact: '',
  }
}

const handleAdd = async () => {
  if (!addForm.value.company || !addForm.value.position) return
  await store.createApplication(addForm.value)
  showAddModal.value = false
  resetAddForm()
}

const openEdit = (app: any) => {
  editingApp.value = { ...app }
  showEditModal.value = true
}

const handleEdit = async () => {
  if (!editingApp.value) return
  await store.updateApplication(editingApp.value.id, editingApp.value)
  showEditModal.value = false
  editingApp.value = null
}

const handleMove = async (appId: string, newStatus: string) => {
  await store.moveApplication(appId, newStatus)
}

const handleDelete = async (appId: string) => {
  await store.deleteApplication(appId)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

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

const onCardDragStart = (appId: string) => {
  dragAppId.value = appId
}

const onCardDragEnd = () => {
  dragAppId.value = null
  dragOverStatus.value = null
}

const onColDragOver = (e: DragEvent, status: string) => {
  e.preventDefault()
  dragOverStatus.value = status
}

const onColDragLeave = () => {
  dragOverStatus.value = null
}

const onColDrop = async (status: string) => {
  if (dragAppId.value && dragOverStatus.value) {
    await store.moveApplication(dragAppId.value, status)
  }
  dragAppId.value = null
  dragOverStatus.value = null
}

onMounted(async () => {
  await store.loadApplications()
  await store.loadStats()
})
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-tracker">
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
              :class="['hm-view-btn', { active: store.viewMode === 'kanban' }]"
              @click="store.viewMode = 'kanban'"
            >
              <TheIcon icon="icon-park-outline:sequence" :size="14" />
              看板
            </button>
            <button
              :class="['hm-view-btn', { active: store.viewMode === 'list' }]"
              @click="store.viewMode = 'list'"
            >
              <TheIcon icon="icon-park-outline:list" :size="14" />
              列表
            </button>
            <button
              :class="['hm-view-btn', { active: store.viewMode === 'timeline' }]"
              @click="store.viewMode = 'timeline'"
            >
              <TheIcon icon="icon-park-outline:time" :size="14" />
              时间线
            </button>
          </div>
          <button class="hm-add-btn" @click="showAddModal = true">
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
          <span class="hm-stat-dot" :style="{ background: store.STATUS_COLORS[status] }"></span>
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
            ></div>
          </div>
          <div class="hm-chart-val" :style="{ color: item.color }">{{ item.value }}</div>
        </div>
      </div>
    </div>

    <div v-if="store.viewMode === 'kanban'" class="hm-kanban">
      <div
        v-for="status in store.STATUS_LIST"
        :key="status"
        :class="['hm-kanban-col', { dragover: dragOverStatus === status }]"
        @dragover="onColDragOver($event, status)"
        @dragleave="onColDragLeave"
        @drop="onColDrop(status)"
      >
        <div class="hm-kanban-col-header">
          <span class="hm-kanban-dot" :style="{ background: store.STATUS_COLORS[status] }"></span>
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
                  确定删除该记录？
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
                <option
                  v-for="s in store.STATUS_LIST"
                  :key="s"
                  :value="s"
                >
                  {{ store.STATUS_LABELS[s] }}
                </option>
              </select>
              <button class="hm-app-edit-btn" @click="openEdit(app)">
                <TheIcon icon="icon-park-outline:edit" :size="12" />
                编辑
              </button>
            </div>
          </div>
          <div v-if="store.getApplicationsByStatus(status).length === 0" class="hm-kanban-empty">
            暂无记录
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="store.viewMode === 'timeline'" class="hm-timeline-view">
      <div v-if="store.timelineApplications.length === 0" class="hm-list-empty">
        <TheIcon icon="icon-park-outline:time" :size="48" color="var(--hm-font-fourth)" />
        <p>暂无求职记录</p>
        <span @click="showAddModal = true">添加第一条记录</span>
      </div>
      <div v-else class="hm-timeline-list">
        <div
          v-for="app in store.timelineApplications"
          :key="app.id"
          class="hm-timeline-item"
        >
          <div class="hm-timeline-dot" :style="{ background: store.STATUS_COLORS[app.status] }"></div>
          <div class="hm-timeline-line"></div>
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
              <button class="hm-timeline-btn" @click="openEdit(app)">编辑</button>
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

    <div v-else class="hm-list-view">
      <div v-if="store.applications.length === 0" class="hm-list-empty">
        <TheIcon icon="icon-park-outline:sequence" :size="48" color="var(--hm-font-fourth)" />
        <p>暂无求职记录</p>
        <span @click="showAddModal = true">添加第一条记录</span>
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
            <button class="hm-list-action" @click="openEdit(app)">编辑</button>
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

    <NModal v-model:show="showAddModal" preset="card" title="添加求职记录" style="width: 480px">
      <NForm label-placement="left" label-width="60">
        <NFormItem label="公司">
          <NInput v-model:value="addForm.company" placeholder="公司名称" />
        </NFormItem>
        <NFormItem label="职位">
          <NInput v-model:value="addForm.position" placeholder="职位名称" />
        </NFormItem>
        <NFormItem label="状态">
          <NSelect v-model:value="addForm.status" :options="statusOptions" />
        </NFormItem>
        <NFormItem label="薪资">
          <NInput v-model:value="addForm.salary" placeholder="如 20-30K" />
        </NFormItem>
        <NFormItem label="地点">
          <NInput v-model:value="addForm.location" placeholder="如 北京" />
        </NFormItem>
        <NFormItem label="渠道">
          <NSelect v-model:value="addForm.source" :options="sourceOptions" clearable placeholder="投递渠道" />
        </NFormItem>
        <NFormItem label="备注">
          <NInput v-model:value="addForm.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <button class="hm-modal-btn" @click="showAddModal = false">取消</button>
          <button class="hm-modal-btn primary" @click="handleAdd">添加</button>
        </div>
      </template>
    </NModal>

    <NModal v-model:show="showEditModal" preset="card" title="编辑求职记录" style="width: 480px">
      <NForm v-if="editingApp" label-placement="left" label-width="60">
        <NFormItem label="公司">
          <NInput v-model:value="editingApp.company" />
        </NFormItem>
        <NFormItem label="职位">
          <NInput v-model:value="editingApp.position" />
        </NFormItem>
        <NFormItem label="状态">
          <NSelect v-model:value="editingApp.status" :options="statusOptions" />
        </NFormItem>
        <NFormItem label="薪资">
          <NInput v-model:value="editingApp.salary" />
        </NFormItem>
        <NFormItem label="地点">
          <NInput v-model:value="editingApp.location" />
        </NFormItem>
        <NFormItem label="渠道">
          <NInput v-model:value="editingApp.source" />
        </NFormItem>
        <NFormItem label="备注">
          <NInput v-model:value="editingApp.notes" type="textarea" :rows="2" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <button class="hm-modal-btn" @click="showEditModal = false">取消</button>
          <button class="hm-modal-btn primary" @click="handleEdit">保存</button>
        </div>
      </template>
    </NModal>
  </div>
  </AppPage>
</template>

<style scoped>
.hm-tracker {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hm-tracker-header {
  padding: 16px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-bottom: 1px solid var(--hm-border-glass);
  flex-shrink: 0;
}

.hm-tracker-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.hm-tracker-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--hm-font-primary);
  letter-spacing: -0.2px;
}

.hm-tracker-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.hm-search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  transition: all 0.3s var(--hm-spring);
}

.hm-search-box:focus-within {
  border-color: var(--hm-brand);
  box-shadow: 0 0 0 3px rgba(10, 89, 247, 0.08);
}

.hm-search-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 12px;
  color: var(--hm-font-primary);
  width: 120px;
  font-family: inherit;
}

.hm-search-input::placeholder {
  color: var(--hm-font-fourth);
}

.hm-view-toggle {
  display: flex;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  overflow: hidden;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
}

.hm-view-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-view-btn.active {
  background: var(--hm-brand);
  color: #fff;
  box-shadow: var(--hm-shadow-brand);
}

.hm-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 16px;
  border: none;
  border-radius: var(--hm-radius-full);
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  box-shadow: var(--hm-shadow-brand);
  transition: all 0.3s var(--hm-spring);
}

.hm-add-btn:hover {
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35);
  transform: translateY(-2px);
}

.hm-add-btn:active {
  transform: translateY(0) scale(0.97);
  transition-duration: 0.1s;
}

.hm-stats-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hm-stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-full);
  font-size: 12px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  transition: all 0.3s var(--hm-spring);
}

.hm-stat-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.hm-stat-chip.total {
  border-color: var(--hm-border-glass);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
}

.hm-stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.hm-stat-label {
  color: var(--hm-font-secondary);
}

.hm-stat-count {
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-chart-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-lg);
  border: 1px solid var(--hm-border-glass);
}

.hm-chart-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hm-chart-label {
  width: 56px;
  font-size: 12px;
  color: var(--hm-font-secondary);
  text-align: right;
  flex-shrink: 0;
}

.hm-chart-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.hm-chart-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s var(--hm-spring);
}

.hm-chart-val {
  width: 24px;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  flex-shrink: 0;
}

.hm-kanban {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 16px;
  overflow-x: auto;
  overflow-y: hidden;
  -ms-overflow-style: none;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}
.hm-kanban::-webkit-scrollbar { height: 6px; }
.hm-kanban::-webkit-scrollbar-track { background: transparent; }
.hm-kanban::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.2s;
}
.hm-kanban:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
}
.hm-kanban::-webkit-scrollbar-thumb:hover {
  background: var(--hm-brand);
}

.hm-kanban-col {
  min-width: 240px;
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  transition: all 0.3s var(--hm-spring);
}

.hm-kanban-col.dragover {
  background: var(--hm-brand-light);
  box-shadow: 0 0 0 2px var(--hm-brand);
}

.hm-kanban-col-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--hm-divider);
}

.hm-kanban-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.hm-kanban-col-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--hm-font-primary);
  flex: 1;
}

.hm-kanban-col-count {
  font-size: 12px;
  color: var(--hm-font-fourth);
  background: rgba(0, 0, 0, 0.04);
  padding: 1px 8px;
  border-radius: var(--hm-radius-full);
}

.hm-kanban-col-body {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  -ms-overflow-style: none;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}
.hm-kanban-col-body::-webkit-scrollbar { width: 4px; }
.hm-kanban-col-body::-webkit-scrollbar-track { background: transparent; }
.hm-kanban-col-body::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 2px;
  transition: background 0.2s;
}
.hm-kanban-col-body:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
}
.hm-kanban-col-body::-webkit-scrollbar-thumb:hover {
  background: var(--hm-brand);
}

.hm-app-card {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-lg);
  border: 1px solid var(--hm-border-glass);
  padding: 12px;
  box-shadow: var(--hm-shadow-layered);
  transition: all 0.3s var(--hm-spring);
  cursor: grab;
}

.hm-app-card.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
}

.hm-app-card:active {
  cursor: grabbing;
}

.hm-app-card:hover {
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-2px);
}

.hm-app-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.hm-app-company {
  font-size: 14px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-app-card-menu {
  display: flex;
  gap: 2px;
}

.hm-app-card-action {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-fourth);
  transition: all 0.25s var(--hm-spring);
}

.hm-app-card-action:hover {
  background: rgba(232, 64, 38, 0.08);
  color: #E84026;
  transform: scale(1.1);
}

.hm-app-position {
  font-size: 13px;
  color: var(--hm-font-secondary);
  margin-bottom: 4px;
}

.hm-app-salary {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-brand);
  margin-bottom: 6px;
}

.hm-app-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--hm-font-fourth);
  margin-bottom: 8px;
}

.hm-app-meta span {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.hm-app-move {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.hm-move-select {
  flex: 1;
  padding: 3px 8px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-sm);
  font-size: 12px;
  color: var(--hm-font-secondary);
  background: var(--hm-bg-primary);
  cursor: pointer;
  outline: none;
  transition: border-color 0.3s var(--hm-spring);
}

.hm-move-select:focus {
  border-color: var(--hm-brand);
}

.hm-app-edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 3px 8px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-sm);
  background: transparent;
  font-size: 12px;
  color: var(--hm-font-tertiary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-app-edit-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  transform: translateY(-1px);
}

.hm-kanban-empty {
  text-align: center;
  padding: 20px 0;
  font-size: 12px;
  color: var(--hm-font-fourth);
}

.hm-list-view {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.hm-list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.hm-list-empty p {
  font-size: 14px;
  color: var(--hm-font-tertiary);
  margin: 12px 0 8px;
}

.hm-list-empty span {
  font-size: 14px;
  color: var(--hm-brand);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
}

.hm-list-empty span:hover {
  transform: translateY(-1px);
}

.hm-list-table {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  overflow: hidden;
}

.hm-list-header {
  display: flex;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid var(--hm-divider);
  font-size: 12px;
  font-weight: 500;
  color: var(--hm-font-tertiary);
}

.hm-list-row {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid var(--hm-divider);
  align-items: center;
  transition: all 0.25s var(--hm-spring);
}

.hm-list-row:last-child {
  border-bottom: none;
}

.hm-list-row:hover {
  background: rgba(10, 89, 247, 0.02);
}

.hm-list-col {
  font-size: 13px;
  color: var(--hm-font-primary);
}

.hm-list-col.company { width: 140px; font-weight: 500; }
.hm-list-col.position { width: 140px; }
.hm-list-col.status { width: 80px; }
.hm-list-col.salary { width: 80px; }
.hm-list-col.location { width: 80px; }
.hm-list-col.source { width: 80px; }
.hm-list-col.date { width: 80px; color: var(--hm-font-fourth); }
.hm-list-col.actions { flex: 1; display: flex; gap: 8px; }

.hm-status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--hm-radius-full);
  font-size: 12px;
  font-weight: 500;
}

.hm-list-action {
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--hm-brand);
  cursor: pointer;
  padding: 2px 4px;
  transition: all 0.25s var(--hm-spring);
}

.hm-list-action.danger {
  color: var(--hm-error);
}

.hm-list-action:hover {
  transform: translateY(-1px);
}

.hm-modal-btn {
  padding: 7px 18px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-secondary);
  font-size: 13px;
  color: var(--hm-font-primary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-modal-btn.primary {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: var(--hm-shadow-brand);
}

.hm-modal-btn.primary:hover {
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .hm-kanban-col {
    min-width: 200px;
    width: 200px;
  }
  .hm-list-col.source,
  .hm-list-col.location {
    display: none;
  }
}

.hm-timeline-view {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.hm-timeline-list {
  max-width: 640px;
  margin: 0 auto;
  position: relative;
}

.hm-timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
  padding-bottom: 24px;
}

.hm-timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
  position: relative;
  z-index: 1;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.hm-timeline-line {
  position: absolute;
  left: 5px;
  top: 18px;
  bottom: 0;
  width: 2px;
  background: var(--hm-divider);
}

.hm-timeline-item:last-child .hm-timeline-line {
  display: none;
}

.hm-timeline-card {
  flex: 1;
  padding: 16px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  transition: all 0.3s var(--hm-spring);
}

.hm-timeline-card:hover {
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-3px);
}

.hm-timeline-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.hm-timeline-company {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-timeline-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--hm-radius-full);
  font-weight: 500;
}

.hm-timeline-position {
  font-size: 13px;
  color: var(--hm-font-secondary);
  margin-bottom: 6px;
}

.hm-timeline-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: var(--hm-font-fourth);
  margin-bottom: 8px;
}

.hm-timeline-actions {
  display: flex;
  gap: 8px;
}

.hm-timeline-btn {
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--hm-brand);
  cursor: pointer;
  padding: 2px 4px;
  transition: all 0.25s var(--hm-spring);
}

.hm-timeline-btn.danger {
  color: var(--hm-error);
}

.hm-timeline-btn:hover {
  transform: translateY(-1px);
}
</style>
