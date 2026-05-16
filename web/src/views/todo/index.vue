<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton, NPopconfirm, NEmpty, NInput, NSelect, NTag,
  NModal, NForm, NFormItem, NDatePicker, NSpace, NRadioGroup, NRadio,
} from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { formatDateTimeShort, formatDueDate } from '@/utils/common/time'

defineOptions({ name: '待办任务' })

const { t } = useI18n()

interface TodoItem {
  id: number
  content: string
  priority: string
  category: string
  due_date: string
  created_at: string
  done: boolean
}

const todoList = ref<TodoItem[]>([])
const loading = ref(false)
const filterCategory = ref<string | null>(null)
const filterPriority = ref<string | null>(null)
const filterDone = ref<string | null>(null)

const showAddModal = ref(false)
const showEditModal = ref(false)
const editingIndex = ref(-1)

const addForm = ref({ content: '', priority: 'medium', category: 'other', due_date: null as string | null })
const editForm = ref({ content: '', priority: 'medium', category: 'other', due_date: null as string | null })

const priorityOptions = computed(() => [
  { label: t('views.todo.priority_high'), value: 'high' },
  { label: t('views.todo.priority_medium'), value: 'medium' },
  { label: t('views.todo.priority_low'), value: 'low' },
])
const categoryOptions = computed(() => [
  { label: t('views.todo.category_work'), value: 'work' },
  { label: t('views.todo.category_study'), value: 'study' },
  { label: t('views.todo.category_life'), value: 'life' },
  { label: t('views.todo.category_job'), value: 'job' },
  { label: t('views.todo.category_other'), value: 'other' },
])
const filterDoneOptions = computed(() => [
  { label: t('views.todo.filter_all'), value: 'all' },
  { label: t('views.todo.filter_undone'), value: 'undone' },
  { label: t('views.todo.filter_done'), value: 'done' },
])

const priorityColor: Record<string, string> = { high: '#E84026', medium: '#ED6F21', low: '#86909C' }
const priorityLabel = computed<Record<string, string>>(() => ({ high: t('views.todo.priority_high'), medium: t('views.todo.priority_medium'), low: t('views.todo.priority_low') }))
const categoryLabel = computed<Record<string, string>>(() => ({ work: t('views.todo.category_work'), study: t('views.todo.category_study'), life: t('views.todo.category_life'), job: t('views.todo.category_job'), other: t('views.todo.category_other') }))
const categoryColor: Record<string, string> = { work: '#0A59F7', study: '#722ED1', life: '#64BB5C', job: '#ED6F21', other: '#86909C' }

const getPriorityTagColor = (p: string) => {
  const c = priorityColor[p] || priorityColor.medium
  return { color: c + '14', textColor: c, borderColor: c + '30' }
}
const getCategoryTagColor = (cat: string) => {
  const c = categoryColor[cat] || categoryColor.other
  return { color: c + '14', textColor: c, borderColor: c + '30' }
}

const stats = computed(() => {
  const total = todoList.value.length
  const done = todoList.value.filter((t) => t.done).length
  const overdue = todoList.value.filter((t) => {
    if (!t.due_date || t.done) return false
    return new Date(t.due_date) < new Date()
  }).length
  return { total, done, undone: total - done, overdue }
})

const progressPercent = computed(() => {
  if (stats.value.total === 0) return 0
  return Math.round((stats.value.done / stats.value.total) * 100)
})

const circumference = 2 * Math.PI * 40
const strokeDashoffset = computed(() => {
  return circumference * (1 - progressPercent.value / 100)
})

const viewMode = ref<'list' | 'calendar'>('list')

const calendarDays = computed(() => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const days: { date: number; todos: TodoItem[]; isToday: boolean }[] = []

  for (let i = 0; i < firstDay; i++) {
    days.push({ date: 0, todos: [], isToday: false })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const dayTodos = todoList.value.filter((t) => t.due_date && t.due_date.startsWith(dateStr))
    days.push({ date: d, todos: dayTodos, isToday: d === now.getDate() })
  }

  return days
})

const calendarMonth = computed(() => {
  const now = new Date()
  return t('views.todo.calendar_month', { year: now.getFullYear(), month: now.getMonth() + 1 })
})

const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

const onDragStart = (index: number) => {
  dragIndex.value = index
}

const onDragOver = (e: DragEvent, index: number) => {
  e.preventDefault()
  dragOverIndex.value = index
}

const onDragEnd = () => {
  dragIndex.value = null
  dragOverIndex.value = null
}

const onDrop = async (targetIndex: number) => {
  if (dragIndex.value === null || dragIndex.value === targetIndex) {
    dragIndex.value = null
    dragOverIndex.value = null
    return
  }
  const item = filteredList.value[dragIndex.value]
  const targetItem = filteredList.value[targetIndex]
  if (item && targetItem) {
    try {
      await Promise.all([
        api.updateTodo({ id: item.id, priority: targetItem.priority }),
        api.updateTodo({ id: targetItem.id, priority: item.priority }),
      ])
      await loadTodos()
    } catch (error) {
      console.error('排序失败', error)
    }
  }
  dragIndex.value = null
  dragOverIndex.value = null
}

const filteredList = computed(() => {
  let list = [...todoList.value]
  if (filterCategory.value) list = list.filter((t) => t.category === filterCategory.value)
  if (filterPriority.value) list = list.filter((t) => t.priority === filterPriority.value)
  if (filterDone.value === 'done') list = list.filter((t) => t.done)
  else if (filterDone.value === 'undone') list = list.filter((t) => !t.done)
  list.sort((a, b) => {
    if (a.done !== b.done) return a.done ? 1 : -1
    const pOrder: Record<string, number> = { high: 0, medium: 1, low: 2 }
    if (pOrder[a.priority] !== pOrder[b.priority]) return pOrder[a.priority] - pOrder[b.priority]
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
  return list
})

const loadTodos = async () => {
  loading.value = true
  try {
    const res = await api.getTodoList()
    todoList.value = (res.data || []).map((t: any, i: number) => ({
      ...t,
      id: t.id ?? i,
      priority: t.priority || 'medium',
      category: t.category || 'other',
      due_date: t.due_date || '',
    }))
  } catch (error) {
    console.error('加载待办失败', error)
  } finally {
    loading.value = false
  }
}

const handleToggle = async (item: TodoItem) => {
  try {
    await api.toggleTodo({ id: item.id })
    await loadTodos()
  } catch (error) {
    console.error('切换状态失败', error)
  }
}

const handleDelete = async (item: TodoItem) => {
  try {
    await api.deleteTodo({ id: item.id })
    window.$message?.success(t('views.todo.msg_deleted'))
    await loadTodos()
  } catch (error) {
    console.error('删除待办失败', error)
  }
}

const handleClearCompleted = async () => {
  try {
    await api.clearCompletedTodos()
    window.$message?.success(t('views.todo.msg_cleared'))
    await loadTodos()
  } catch (error) {
    console.error('清除失败', error)
  }
}

const openAddModal = () => {
  addForm.value = { content: '', priority: 'medium', category: 'other', due_date: null }
  showAddModal.value = true
}

const handleAdd = async () => {
  if (!addForm.value.content.trim()) return
  try {
    await api.createTodo(addForm.value)
    showAddModal.value = false
    window.$message?.success(t('views.todo.msg_created'))
    await loadTodos()
  } catch (error) {
    console.error('创建待办失败', error)
  }
}

const normalizeDueDate = (dateStr: string | null): string | null => {
  if (!dateStr) return null
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return `${dateStr} 00:00:00`
  return dateStr
}

const openEditModal = (item: TodoItem) => {
  editForm.value = {
    content: item.content,
    priority: item.priority || 'medium',
    category: item.category || 'other',
    due_date: normalizeDueDate(item.due_date),
  }
  editingIndex.value = item.id
  showEditModal.value = true
}

const handleEdit = async () => {
  if (!editForm.value.content.trim()) return
  try {
    await api.updateTodo({ id: editingIndex.value, ...editForm.value })
    showEditModal.value = false
    window.$message?.success(t('views.todo.msg_updated'))
    await loadTodos()
  } catch (error) {
    console.error('更新待办失败', error)
  }
}

const isOverdue = (item: TodoItem) => {
  if (!item.due_date || item.done) return false
  return new Date(item.due_date) < new Date()
}

onMounted(() => {
  loadTodos()
})
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-page-container">
    <div class="hm-page-header">
      <div>
        <h1 class="hm-page-title">{{ t('views.todo.page_title') }}</h1>
        <p class="hm-page-subtitle">{{ t('views.todo.total_count', { total: stats.total, undone: stats.undone }) }}</p>
      </div>
      <div class="hm-todo-actions">
        <div class="hm-view-toggle">
          <button
            :class="['hm-view-btn', { active: viewMode === 'list' }]"
            @click="viewMode = 'list'"
          >
            <TheIcon icon="icon-park-outline:list" :size="14" />
            {{ t('views.todo.list_view') }}
          </button>
          <button
            :class="['hm-view-btn', { active: viewMode === 'calendar' }]"
            @click="viewMode = 'calendar'"
          >
            <TheIcon icon="icon-park-outline:calendar" :size="14" />
            {{ t('views.todo.calendar_view') }}
          </button>
        </div>
        <button class="hm-action-btn primary" @click="openAddModal">
          <TheIcon icon="icon-park-outline:plus" :size="16" color="#fff" />
          {{ t('views.todo.btn_new') }}
        </button>
        <button class="hm-action-btn" @click="loadTodos" :disabled="loading">
          <TheIcon icon="icon-park-outline:refresh" :size="16" />
        </button>
      </div>
    </div>

    <div class="hm-stats-row">
      <div class="hm-stat-card">
        <div class="hm-stat-icon" style="background: rgba(10,89,247,0.08)">
          <TheIcon icon="icon-park-outline:list" :size="20" color="#0A59F7" />
        </div>
        <div class="hm-stat-info">
          <div class="hm-stat-value">{{ stats.total }}</div>
          <div class="hm-stat-label">{{ t('views.todo.stat_all') }}</div>
        </div>
      </div>
      <div class="hm-stat-card">
        <div class="hm-stat-icon" style="background: rgba(237,111,33,0.08)">
          <TheIcon icon="icon-park-outline:time" :size="20" color="#ED6F21" />
        </div>
        <div class="hm-stat-info">
          <div class="hm-stat-value" style="color: #ED6F21">{{ stats.undone }}</div>
          <div class="hm-stat-label">{{ t('views.todo.stat_undone') }}</div>
        </div>
      </div>
      <div class="hm-stat-card">
        <div class="hm-stat-icon" style="background: rgba(100,187,92,0.08)">
          <TheIcon icon="icon-park-outline:check-one" :size="20" color="#64BB5C" />
        </div>
        <div class="hm-stat-info">
          <div class="hm-stat-value" style="color: #64BB5C">{{ stats.done }}</div>
          <div class="hm-stat-label">{{ t('views.todo.stat_done') }}</div>
        </div>
      </div>
      <div class="hm-stat-card">
        <div class="hm-stat-icon" style="background: rgba(232,64,38,0.08)">
          <TheIcon icon="icon-park-outline:caution" :size="20" color="#E84026" />
        </div>
        <div class="hm-stat-info">
          <div class="hm-stat-value" style="color: #E84026">{{ stats.overdue }}</div>
          <div class="hm-stat-label">{{ t('views.todo.stat_overdue') }}</div>
        </div>
      </div>
      <div class="hm-progress-card">
        <svg class="hm-progress-ring" width="88" height="88" viewBox="0 0 88 88">
          <circle cx="44" cy="44" r="40" fill="none" stroke="var(--hm-border)" stroke-width="6" />
          <circle
            cx="44" cy="44" r="40" fill="none"
            stroke="#0A59F7" stroke-width="6"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="strokeDashoffset"
            transform="rotate(-90 44 44)"
            class="hm-progress-arc"
          />
        </svg>
        <div class="hm-progress-text">
          <span class="hm-progress-num">{{ progressPercent }}</span>
          <span class="hm-progress-unit">%</span>
        </div>
        <div class="hm-progress-label">{{ t('views.todo.progress_label') }}</div>
      </div>
    </div>

    <div class="hm-filter-row">
      <NSelect
        v-model:value="filterDone"
        :options="filterDoneOptions"
        :placeholder="t('views.todo.filter_status')"
        clearable
        size="small"
        style="width: 110px"
      />
      <NSelect
        v-model:value="filterPriority"
        :options="priorityOptions"
        :placeholder="t('views.todo.filter_priority')"
        clearable
        size="small"
        style="width: 100px"
      />
      <NSelect
        v-model:value="filterCategory"
        :options="categoryOptions"
        :placeholder="t('views.todo.filter_category')"
        clearable
        size="small"
        style="width: 100px"
      />
      <NPopconfirm v-if="stats.done > 0" @positive-click="handleClearCompleted">
        <template #trigger>
          <button class="hm-filter-chip danger">{{ t('views.todo.btn_clear_done') }}</button>
        </template>
        {{ t('views.todo.confirm_clear_done') }}
      </NPopconfirm>
    </div>

    <div v-if="viewMode === 'calendar'" class="hm-calendar-view">
      <div class="hm-calendar-header">
        <span class="hm-calendar-month">{{ calendarMonth }}</span>
      </div>
      <div class="hm-calendar-grid">
        <div class="hm-calendar-weekday" v-for="d in t('views.todo.weekday_names').split(',')" :key="d">{{ d }}</div>
        <div
          v-for="(day, idx) in calendarDays"
          :key="idx"
          :class="['hm-calendar-day', { today: day.isToday, empty: day.date === 0 }]"
        >
          <span v-if="day.date" class="hm-day-num">{{ day.date }}</span>
          <div v-if="day.todos.length" class="hm-day-todos">
            <div
              v-for="t in day.todos.slice(0, 2)"
              :key="t.id"
              :class="['hm-day-todo', { done: t.done }]"
            >
              {{ t.content.slice(0, 6) }}
            </div>
            <div v-if="day.todos.length > 2" class="hm-day-more">+{{ day.todos.length - 2 }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="hm-todo-list">
      <div v-if="filteredList.length === 0 && !loading" class="hm-todo-empty">
        <TheIcon icon="icon-park-outline:todo" :size="48" color="var(--hm-font-fourth)" />
        <p>{{ t('views.todo.empty_title') }}</p>
        <div class="hm-empty-actions">
          <button class="hm-action-btn primary small" @click="openAddModal">{{ t('views.todo.btn_new_todo') }}</button>
          <button class="hm-action-btn small" @click="$router.push('/agent-chat')">{{ t('views.todo.btn_ai_create') }}</button>
        </div>
      </div>

      <div
        v-for="(item, idx) in filteredList"
        :key="item.id"
        :class="['hm-todo-item', { done: item.done, overdue: isOverdue(item), dragging: dragIndex === idx, dragover: dragOverIndex === idx }]"
        draggable="true"
        @dragstart="onDragStart(idx)"
        @dragover="onDragOver($event, idx)"
        @dragend="onDragEnd"
        @drop="onDrop(idx)"
      >
        <div class="hm-todo-left" @click="handleToggle(item)">
          <div :class="['hm-checkbox', { checked: item.done }]">
            <TheIcon v-if="item.done" icon="icon-park-outline:check-one" :size="14" color="#fff" />
          </div>
          <div class="hm-todo-content">
            <div class="hm-todo-tags">
              <NTag :color="getPriorityTagColor(item.priority)" size="small" round>
                {{ priorityLabel[item.priority] || t('views.todo.priority_medium') }}
              </NTag>
              <NTag :color="getCategoryTagColor(item.category)" size="small" round>
                {{ categoryLabel[item.category] || t('views.todo.category_other') }}
              </NTag>
              <NTag v-if="item.due_date" :type="isOverdue(item) ? 'error' : 'default'" size="small" round>
                {{ isOverdue(item) ? t('views.todo.tag_overdue') : formatDueDate(item.due_date) }}
              </NTag>
            </div>
            <span class="hm-todo-text">{{ item.content }}</span>
            <span class="hm-todo-time">{{ formatDateTimeShort(item.created_at) }}</span>
          </div>
        </div>
        <div class="hm-todo-right">
          <button class="hm-icon-btn" @click.stop="openEditModal(item)">
            <TheIcon icon="icon-park-outline:edit" :size="16" />
          </button>
          <NPopconfirm @positive-click="handleDelete(item)">
            <template #trigger>
              <button class="hm-icon-btn danger" @click.stop>
                <TheIcon icon="icon-park-outline:delete" :size="16" />
              </button>
            </template>
            {{ t('views.todo.confirm_delete') }}
          </NPopconfirm>
        </div>
      </div>
    </div>

    <NModal v-model:show="showAddModal" preset="dialog" :title="t('views.todo.modal_add_title')" :positive-text="t('views.todo.modal_btn_create')" :negative-text="t('views.todo.modal_btn_cancel')" @positive-click="handleAdd">
      <NForm label-placement="left" label-width="60">
        <NFormItem :label="t('views.todo.form_content')">
          <NInput v-model:value="addForm.content" :placeholder="t('views.todo.form_content_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.todo.form_priority')">
          <NRadioGroup v-model:value="addForm.priority">
            <NSpace>
              <NRadio value="high">{{ t('views.todo.priority_high') }}</NRadio>
              <NRadio value="medium">{{ t('views.todo.priority_medium') }}</NRadio>
              <NRadio value="low">{{ t('views.todo.priority_low') }}</NRadio>
            </NSpace>
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="t('views.todo.form_category')">
          <NSelect v-model:value="addForm.category" :options="categoryOptions" />
        </NFormItem>
        <NFormItem :label="t('views.todo.form_due_date')">
          <NDatePicker v-model:formatted-value="addForm.due_date" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" clearable style="width: 100%" />
        </NFormItem>
      </NForm>
    </NModal>

    <NModal v-model:show="showEditModal" preset="dialog" :title="t('views.todo.modal_edit_title')" :positive-text="t('views.todo.modal_btn_save')" :negative-text="t('views.todo.modal_btn_cancel')" @positive-click="handleEdit">
      <NForm label-placement="left" label-width="60">
        <NFormItem :label="t('views.todo.form_content')">
          <NInput v-model:value="editForm.content" :placeholder="t('views.todo.form_content_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.todo.form_priority')">
          <NRadioGroup v-model:value="editForm.priority">
            <NSpace>
              <NRadio value="high">{{ t('views.todo.priority_high') }}</NRadio>
              <NRadio value="medium">{{ t('views.todo.priority_medium') }}</NRadio>
              <NRadio value="low">{{ t('views.todo.priority_low') }}</NRadio>
            </NSpace>
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="t('views.todo.form_category')">
          <NSelect v-model:value="editForm.category" :options="categoryOptions" />
        </NFormItem>
        <NFormItem :label="t('views.todo.form_due_date')">
          <NDatePicker v-model:formatted-value="editForm.due_date" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" clearable style="width: 100%" />
        </NFormItem>
      </NForm>
    </NModal>
  </div>
  </AppPage>
</template>

<style scoped>
.hm-todo-actions {
  display: flex;
  gap: 8px;
}

.hm-stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.hm-progress-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 18px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  position: relative;
  transition: all 0.35s var(--hm-spring);
}

.hm-progress-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--hm-shadow-layered-hover);
}

.hm-progress-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.15;
}

.hm-progress-arc {
  transition: stroke-dashoffset 0.8s var(--hm-spring);
}

.hm-progress-text {
  display: flex;
  align-items: baseline;
  justify-content: center;
}

.hm-progress-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--hm-brand);
}

.hm-progress-unit {
  font-size: 14px;
  color: var(--hm-font-tertiary);
  margin-left: 2px;
}

.hm-progress-label {
  font-size: 12px;
  color: var(--hm-font-tertiary);
  margin-top: 4px;
  font-weight: 500;
}

.hm-calendar-view {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  padding: 22px;
  box-shadow: var(--hm-shadow-layered);
}

.hm-calendar-header {
  margin-bottom: 16px;
}

.hm-calendar-month {
  font-size: 16px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.hm-calendar-weekday {
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--hm-font-fourth);
  padding: 8px 0;
}

.hm-calendar-day {
  min-height: 72px;
  padding: 6px;
  border-radius: var(--hm-radius-sm);
  background: var(--hm-bg-container-secondary);
  transition: all 0.2s var(--hm-spring);
}

.hm-calendar-day.empty {
  background: transparent;
}

.hm-calendar-day.today {
  background: var(--hm-brand-light);
  border: 1px solid color-mix(in srgb, var(--hm-brand) 20%, transparent);
}

.hm-day-num {
  font-size: 12px;
  font-weight: 500;
  color: var(--hm-font-secondary);
}

.hm-calendar-day.today .hm-day-num {
  color: var(--hm-brand);
  font-weight: 700;
}

.hm-day-todos {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
}

.hm-day-todo {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  background: var(--hm-brand-bg-light);
  color: var(--hm-font-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-day-todo.done {
  text-decoration: line-through;
  opacity: 0.5;
}

.hm-day-more {
  font-size: 10px;
  color: var(--hm-font-fourth);
  text-align: center;
}

.hm-todo-item.dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.hm-todo-item.dragover {
  border-top: 2px solid var(--hm-brand);
}

.hm-filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.hm-todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hm-todo-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 0;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
}

.hm-todo-empty p {
  font-size: 14px;
  color: var(--hm-font-tertiary);
  margin: 12px 0 16px;
}

.hm-empty-actions {
  display: flex;
  gap: 8px;
}

.hm-todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  transition: all 0.3s var(--hm-spring);
}

.hm-todo-item:hover {
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-2px);
}

.hm-todo-item:active {
  transform: translateY(0) scale(0.99);
  transition-duration: 0.1s;
}

.hm-todo-item.done {
  opacity: 0.55;
}

.hm-todo-item.overdue {
  background: var(--hm-danger-hover-bg);
  border-color: rgba(232, 64, 38, 0.15);
}

.hm-todo-left {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.hm-checkbox {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 2px solid var(--hm-border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s var(--hm-spring);
}

.hm-checkbox.checked {
  background: var(--hm-brand-gradient);
  border-color: transparent;
  box-shadow: var(--hm-shadow-brand);
}

.hm-todo-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.hm-todo-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.hm-todo-text {
  font-size: 14px;
  color: var(--hm-font-primary);
  line-height: 1.5;
  word-break: break-all;
}

.hm-todo-item.done .hm-todo-text {
  text-decoration: line-through;
  color: var(--hm-font-tertiary);
}

.hm-todo-time {
  font-size: 12px;
  color: var(--hm-font-fourth);
}

.hm-todo-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .hm-page-container {
    padding: 16px 12px;
  }
  .hm-page-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 16px;
    gap: 12px;
    overflow: visible;
  }
  .hm-todo-actions {
    width: 100%;
    flex-wrap: wrap;
    gap: 6px;
    overflow: visible;
  }
  .hm-view-toggle {
    flex-shrink: 0;
  }
  .hm-view-btn {
    padding: 5px 10px;
    font-size: 12px;
    gap: 3px;
    white-space: nowrap;
  }
  .hm-todo-actions .hm-action-btn {
    flex-shrink: 0;
    white-space: nowrap;
  }
  .hm-page-title {
    font-size: 22px;
  }
  .hm-stats-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  .hm-stat-card {
    padding: 12px;
  }
  .hm-stat-icon {
    width: 36px;
    height: 36px;
  }
  .hm-stat-value {
    font-size: 20px;
  }
  .hm-progress-card {
    grid-column: span 2;
    flex-direction: row;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
  }
  .hm-progress-ring {
    position: static;
    transform: none;
    width: 48px;
    height: 48px;
  }
  .hm-progress-num {
    font-size: 22px;
  }
  .hm-progress-unit {
    font-size: 12px;
  }
  .hm-progress-label {
    margin-top: 0;
    margin-left: 4px;
  }
  .hm-progress-text {
    align-items: baseline;
  }
  .hm-filter-row {
    gap: 6px;
  }
  .hm-todo-item {
    padding: 12px 14px;
  }
  .hm-calendar-day {
    min-height: 56px;
    padding: 4px;
  }
  .hm-day-todo {
    font-size: 9px;
  }
}

@media (max-width: 480px) {
  .hm-stats-row {
    grid-template-columns: 1fr 1fr;
  }
  .hm-progress-card {
    grid-column: span 2;
    gap: 8px;
    padding: 10px 12px;
  }
  .hm-progress-ring {
    width: 40px;
    height: 40px;
  }
  .hm-progress-num {
    font-size: 18px;
  }
  .hm-todo-right {
    gap: 2px;
  }
  .hm-icon-btn {
    width: 28px;
    height: 28px;
  }
  .hm-todo-tags {
    gap: 2px;
  }
}
</style>
