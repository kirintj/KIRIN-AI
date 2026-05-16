<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { formatRelativeTime } from '@/utils/common/time'

const { t } = useI18n()
const userStore = useUserStore()
const router = useRouter()

const userInfo = ref<any>(null)
const recentConversations = ref<any[]>([])
const dashboardData = ref<any>(null)
const weeklyData = ref<any>(null)
const loading = ref(true)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return t('views.workbench.greeting_night')
  if (hour < 12) return t('views.workbench.greeting_morning')
  if (hour < 14) return t('views.workbench.greeting_noon')
  if (hour < 18) return t('views.workbench.greeting_afternoon')
  return t('views.workbench.greeting_evening')
})

const todayDate = computed(() => {
  const now = new Date()
  const weekDays = t('views.workbench.weekday_names').split(',')
  const weekDay = weekDays[now.getDay()]
  return t('views.workbench.date_format', { month: now.getMonth() + 1, day: now.getDate(), weekday: weekDay })
})

const todoProgress = computed(() => {
  if (!dashboardData.value?.todos) return 0
  const { done, total } = dashboardData.value.todos
  return total > 0 ? Math.round((done / total) * 100) : 0
})

const circumference = 2 * Math.PI * 36
const strokeDashoffset = computed(() => {
  const progress = todoProgress.value / 100
  return circumference * (1 - progress)
})

const weeklyChartBars = computed(() => {
  const days = Array.isArray(weeklyData.value) ? weeklyData.value : weeklyData.value?.days || []
  if (!days.length) return []
  const maxVal = Math.max(...days.map((d: any) => d.count || 0), 1)
  return days.map((d: any) => ({
    ...d,
    label: d.label || d.date,
    count: d.count || 0,
    height: Math.max(((d.count || 0) / maxVal) * 100, 4),
  }))
})

const activityTimeline = computed(() => {
  const items: { icon: string; color: string; text: string; time: string }[] = []
  if (dashboardData.value?.tracker?.recent) {
    for (const app of dashboardData.value.tracker.recent.slice(0, 3)) {
      items.push({
        icon: 'icon-park-outline:sequence',
        color: '#E84026',
        text: t('views.workbench.applied_company', { company: app.company, position: app.position }),
        time: formatRelativeTime(app.created_at),
      })
    }
  }
  if (dashboardData.value?.todos?.recent) {
    for (const todo of dashboardData.value.todos.recent.slice(0, 2)) {
      items.push({
        icon: 'icon-park-outline:data-arrival',
        color: '#64BB5C',
        text: todo.done ? t('views.workbench.completed_todo', { content: todo.content }) : t('views.workbench.created_todo', { content: todo.content }),
        time: formatRelativeTime(todo.created_at),
      })
    }
  }
  return items.slice(0, 5)
})

const loadUserInfo = async () => {
  try {
    await userStore.getUserInfo()
    userInfo.value = userStore.userInfo
  } catch (error) {
    console.error('加载用户信息失败', error)
  }
}

const loadRecentConversations = async () => {
  try {
    const res = await api.getRecentConversations({ limit: 5 })
    recentConversations.value = res.data || []
  } catch (error) {
    console.error('加载最近对话失败', error)
  }
}

const loadDashboard = async () => {
  try {
    const res = await api.getDashboardOverview()
    dashboardData.value = res.data || null
  } catch (error) {
    console.error('加载仪表盘数据失败', error)
  }
}

const loadWeeklyActivity = async () => {
  try {
    const res = await api.getWeeklyActivity()
    weeklyData.value = res.data || null
  } catch (error) {
    console.error('加载周活动数据失败', error)
  }
}

const goToAIChat = () => router.push('/agent-chat')
const goToKnowledge = () => router.push('/knowledge')
const goToTodo = () => router.push('/todo')
const goToSettings = () => router.push('/knowledge')
const goToJobAssistant = () => router.push('/job-assistant')
const goToTracker = () => router.push('/tracker')
const goToInterviewSim = () => router.push('/interview-sim')
const goToResumeExport = () => router.push('/job-assistant')

const quickActions = computed(() => [
  { label: t('views.workbench.quick_interview'), icon: 'icon-park-outline:book-open', color: '#0A59F7', action: () => router.push('/agent-chat') },
  { label: t('views.workbench.quick_tracker'), icon: 'icon-park-outline:log', color: '#E84026', action: goToTracker },
  { label: t('views.workbench.quick_todo'), icon: 'icon-park-outline:data-arrival', color: '#64BB5C', action: goToTodo },
  { label: t('views.workbench.quick_resume'), icon: 'icon-park-outline:redo', color: '#722ED1', action: goToJobAssistant },
])

const featureGrid = computed(() => [
  { label: t('views.workbench.feature_chat'), desc: t('views.workbench.feature_chat_desc'), icon: 'icon-park-outline:topic', color: '#0A59F7', action: goToAIChat },
  { label: t('views.workbench.feature_knowledge'), desc: t('views.workbench.feature_knowledge_desc'), icon: 'icon-park-outline:data', color: '#722ED1', action: goToKnowledge },
  { label: t('views.workbench.feature_todo'), desc: t('views.workbench.feature_todo_desc'), icon: 'icon-park-outline:data-arrival', color: '#64BB5C', action: goToTodo },
  { label: t('views.workbench.feature_tracker'), desc: t('views.workbench.feature_tracker_desc'), icon: 'icon-park-outline:log', color: '#E84026', action: goToTracker },
  { label: t('views.workbench.feature_interview'), desc: t('views.workbench.feature_interview_desc'), icon: 'icon-park-outline:form-one', color: '#722ED1', action: goToInterviewSim },
  { label: t('views.workbench.feature_job_assistant'), desc: t('views.workbench.feature_job_assistant_desc'), icon: 'icon-park-outline:robot', color: '#ED6F21', action: goToJobAssistant },
  { label: t('views.workbench.feature_resume_export'), desc: t('views.workbench.feature_resume_export_desc'), icon: 'icon-park-outline:export', color: '#0A59F7', action: goToResumeExport },
  { label: t('views.workbench.feature_settings'), desc: t('views.workbench.feature_settings_desc'), icon: 'icon-park-outline:setting-two', color: '#86909C', action: goToSettings },
])

const statCards = computed(() => [
  { label: t('views.workbench.stat_total_applications'), key: 'tracker', icon: 'icon-park-outline:share-sys', color: '#0A59F7', getValue: (d: any) => d?.tracker?.total || 0 },
  { label: t('views.workbench.stat_interviewing'), key: 'interviewing', icon: 'icon-park-outline:push-door', color: '#ED6F21', getValue: (d: any) => d?.tracker?.by_status?.interview || 0 },
  { label: t('views.workbench.stat_offer'), key: 'offer', icon: 'icon-park-outline:check-one', color: '#64BB5C', getValue: (d: any) => d?.tracker?.by_status?.offer || 0 },
  { label: t('views.workbench.stat_todo_done'), key: 'todos', icon: 'icon-park-outline:data-arrival', color: '#722ED1', getValue: (d: any) => d?.todos?.done || 0 },
])

onMounted(async () => {
  loading.value = true
  await Promise.allSettled([
    loadUserInfo(),
    loadRecentConversations(),
    loadDashboard(),
    loadWeeklyActivity(),
  ])
  loading.value = false
})
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-workbench">
    <div class="hm-wb-header">
      <div class="hm-wb-header-glow"></div>
      <div class="hm-wb-greeting">
        <h1 class="hm-wb-title">{{ greeting }}，{{ userInfo?.username || t('views.workbench.default_user') }}</h1>
        <p class="hm-wb-subtitle">{{ todayDate }} · {{ t('views.workbench.ai_assistant_subtitle') }}</p>
      </div>
      <div class="hm-wb-header-right">
        <div class="hm-wb-quick-actions">
          <button
            v-for="action in quickActions"
            :key="action.label"
            class="hm-wb-quick-btn"
            @click="action.action"
          >
            <div class="hm-wb-quick-icon" :style="{ background: action.color + '14' }">
              <TheIcon :icon="action.icon" :size="14" :color="action.color" />
            </div>
            <span>{{ action.label }}</span>
          </button>
        </div>
        <div class="hm-wb-avatar">
          <TheIcon icon="icon-park-outline:user" :size="28" color="var(--hm-font-on-brand)" />
        </div>
      </div>
    </div>

    <div v-if="loading" class="hm-wb-skeleton">
      <div class="hm-skeleton-row">
        <div v-for="i in 4" :key="i" class="hm-skeleton-card"></div>
      </div>
      <div class="hm-skeleton-row" style="margin-top: 16px">
        <div class="hm-skeleton-wide"></div>
        <div class="hm-skeleton-narrow"></div>
      </div>
    </div>

    <template v-else>
      <div v-if="dashboardData" class="hm-wb-section hm-wb-fade-in">
        <div class="hm-wb-section-header">
          <h2 class="hm-wb-section-title">{{ t('views.workbench.data_overview') }}</h2>
          <div class="hm-wb-progress-ring-wrap">
            <svg class="hm-wb-progress-ring" width="44" height="44" viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="24" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="8" />
              <circle
                cx="40" cy="40" r="24" fill="none"
                stroke="var(--hm-brand)" stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="strokeDashoffset"
                transform="rotate(-90 40 40)"
                class="hm-wb-ring-progress"
              />
            </svg>
            <span class="hm-wb-ring-text">{{ todoProgress }}%</span>
          </div>
        </div>
        <div class="hm-wb-stats-grid">
          <div
            v-for="stat in statCards"
            :key="stat.key"
            class="hm-wb-stat-card"
          >
            <div class="hm-wb-stat-icon" :style="{ background: stat.color + '14' }">
              <TheIcon :icon="stat.icon" :size="20" :color="stat.color" />
            </div>
            <div class="hm-wb-stat-value">{{ stat.getValue(dashboardData) }}</div>
            <div class="hm-wb-stat-label">{{ stat.label }}</div>
          </div>
        </div>

        <div v-if="dashboardData.tracker" class="hm-wb-tracker-bar">
          <div
            v-for="(label, status) in dashboardData.tracker.status_labels"
            :key="status"
            class="hm-wb-bar-segment"
            :style="{
              width: dashboardData.tracker.total > 0 ? (dashboardData.tracker.by_status[status] / dashboardData.tracker.total * 100) + '%' : '0%',
              background: dashboardData.tracker.status_colors[status],
            }"
            :title="`${label}: ${dashboardData.tracker.by_status[status] || 0}`"
          ></div>
        </div>
        <div v-if="dashboardData.tracker" class="hm-wb-bar-legend">
          <span
            v-for="(label, status) in dashboardData.tracker.status_labels"
            :key="status"
            class="hm-wb-legend-item"
          >
            <span class="hm-wb-legend-dot" :style="{ background: dashboardData.tracker.status_colors[status] }"></span>
            {{ label }} {{ dashboardData.tracker.by_status[status] || 0 }}
          </span>
        </div>
      </div>

      <div class="hm-wb-two-col hm-wb-fade-in" style="animation-delay: 0.1s">
        <div class="hm-wb-section">
          <h2 class="hm-wb-section-title">{{ t('views.workbench.weekly_activity') }}</h2>
          <div class="hm-wb-chart-card">
            <div v-if="weeklyChartBars.length > 0" class="hm-wb-chart">
              <div
                v-for="(bar, idx) in weeklyChartBars"
                :key="idx"
                class="hm-wb-chart-col"
              >
                <div class="hm-wb-chart-bar-wrap">
                  <div
                    class="hm-wb-chart-bar"
                    :style="{ height: bar.height + '%', background: idx === weeklyChartBars.length - 1 ? 'var(--hm-brand)' : 'var(--hm-brand-light)' }"
                  ></div>
                </div>
                <span class="hm-wb-chart-label">{{ bar.label }}</span>
              </div>
            </div>
            <div v-else class="hm-wb-chart-empty">
              <div class="hm-empty-state">
                <div class="hm-empty-state-icon">
                  <TheIcon icon="icon-park-outline:chart-bar" :size="32" color="var(--hm-font-fourth)" />
                </div>
                <div class="hm-empty-state-title">{{ t('views.workbench.no_activity_data') }}</div>
                <div class="hm-empty-state-desc">{{ t('views.workbench.no_activity_desc') }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="hm-wb-section">
          <h2 class="hm-wb-section-title">{{ t('views.workbench.recent_activity') }}</h2>
          <div class="hm-wb-timeline-card">
            <div v-if="activityTimeline.length > 0" class="hm-wb-timeline">
              <div
                v-for="(item, idx) in activityTimeline"
                :key="idx"
                class="hm-wb-timeline-item"
              >
                <div class="hm-wb-timeline-dot" :style="{ background: item.color }"></div>
                <div v-if="idx < activityTimeline.length - 1" class="hm-wb-timeline-line"></div>
                <div class="hm-wb-timeline-content">
                  <div class="hm-wb-timeline-icon" :style="{ background: item.color + '14' }">
                    <TheIcon :icon="item.icon" :size="12" :color="item.color" />
                  </div>
                  <span class="hm-wb-timeline-text">{{ item.text }}</span>
                  <span class="hm-wb-timeline-time">{{ item.time }}</span>
                </div>
              </div>
            </div>
            <div v-else class="hm-wb-chart-empty">
              <div class="hm-empty-state">
                <div class="hm-empty-state-icon">
                  <TheIcon icon="icon-park-outline:time" :size="32" color="var(--hm-font-fourth)" />
                </div>
                <div class="hm-empty-state-title">{{ t('views.workbench.no_activity') }}</div>
                <div class="hm-empty-state-desc">{{ t('views.workbench.no_activity_desc2') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="hm-wb-section hm-wb-fade-in" style="animation-delay: 0.2s">
        <h2 class="hm-wb-section-title">{{ t('views.workbench.feature_center') }}</h2>
        <div class="hm-wb-feature-grid">
          <div
            v-for="item in featureGrid"
            :key="item.label"
            class="hm-wb-feature-card"
            @click="item.action"
          >
            <div class="hm-wb-feature-shimmer"></div>
            <div class="hm-wb-feature-icon" :style="{ background: item.color + '14' }">
              <TheIcon :icon="item.icon" :size="24" :color="item.color" />
            </div>
            <div class="hm-wb-feature-label">{{ item.label }}</div>
            <div class="hm-wb-feature-desc">{{ item.desc }}</div>
          </div>
        </div>
      </div>

      <div class="hm-wb-section hm-wb-fade-in" style="animation-delay: 0.3s">
        <div class="hm-wb-section-header">
          <h2 class="hm-wb-section-title">{{ t('views.workbench.recent_conversations') }}</h2>
          <button class="hm-wb-view-all" @click="goToAIChat">{{ t('views.workbench.view_all') }}</button>
        </div>
        <div class="hm-wb-history-card">
          <div v-if="recentConversations.length === 0" class="hm-empty-state">
            <div class="hm-empty-state-icon">
              <TheIcon icon="icon-park-outline:history" :size="32" color="var(--hm-font-fourth)" />
            </div>
            <div class="hm-empty-state-title">{{ t('views.workbench.no_conversations') }}</div>
            <div class="hm-empty-state-desc">{{ t('views.workbench.no_conversations_desc') }}</div>
            <div class="hm-empty-state-action">
              <button class="hm-action-btn primary" @click="goToAIChat">
                <TheIcon icon="icon-park-outline:chat" :size="14" color="#fff" />
                {{ t('views.workbench.start_conversation') }}
              </button>
            </div>
          </div>
          <div v-else class="hm-wb-conv-list">
            <div
              v-for="conv in recentConversations"
              :key="conv.id"
              class="hm-wb-conv-item"
              @click="goToAIChat"
            >
              <div class="hm-wb-conv-icon">
                <TheIcon icon="icon-park-outline:chat" :size="18" color="var(--hm-brand)" />
              </div>
              <div class="hm-wb-conv-info">
                <div class="hm-wb-conv-title">{{ conv.title || t('views.workbench.new_conversation') }}</div>
                <div class="hm-wb-conv-meta">{{ t('views.workbench.messages_count', { count: conv.message_count || 0 }) }}</div>
              </div>
              <div class="hm-wb-conv-time">{{ formatRelativeTime(conv.updated_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
  </AppPage>
</template>

<style scoped>
.hm-workbench {
  width: 100%;
  margin: 0 auto;
  padding: 32px 28px;
}

/* ── 头部区域 ── */
.hm-wb-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding: 24px 28px;
  border-radius: var(--hm-radius-xl);
  background: var(--hm-bg-glass);
  backdrop-filter: blur(20px) saturate(1.8);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  border: 1px solid var(--hm-border-glass);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 8px 24px rgba(10, 89, 247, 0.06);
  overflow: hidden;
}

.hm-wb-header-glow {
  position: absolute;
  top: -40px;
  right: -20px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(10, 89, 247, 0.12) 0%, transparent 70%);
  pointer-events: none;
  animation: hm-glow-breathe 4s ease-in-out infinite;
}

@keyframes hm-glow-breathe {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.12); }
}

.hm-wb-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
  animation: hm-title-in 0.6s var(--hm-spring) both;
}

@keyframes hm-title-in {
  from { opacity: 0; transform: translateY(10px) scale(0.96); filter: blur(3px); }
  to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}

.hm-wb-subtitle {
  font-size: 14px;
  color: var(--hm-font-tertiary);
  animation: hm-subtitle-in 0.55s var(--hm-spring) 0.08s both;
}

@keyframes hm-subtitle-in {
  from { opacity: 0; transform: translateY(8px); filter: blur(2px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

.hm-wb-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hm-wb-quick-actions {
  display: flex;
  gap: 8px;
}

.hm-wb-quick-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 1px solid var(--hm-divider);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: blur(8px);
  font-size: 12px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.hm-wb-quick-btn::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: rgba(10, 89, 247, 0);
  transition: background 0.3s;
}

.hm-wb-quick-btn:hover {
  border-color: rgba(10, 89, 247, 0.2);
  color: var(--hm-brand);
  transform: translateY(-1px);
  box-shadow: var(--hm-brand-shadow-hover);
}

.hm-wb-quick-btn:hover::after {
  background: var(--hm-brand-bg-light);
}

.hm-wb-quick-btn:active {
  transform: translateY(0) scale(0.94);
  transition-duration: 0.08s;
}

.hm-wb-quick-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hm-wb-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--hm-radius-full);
  background: var(--hm-brand-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--hm-shadow-brand);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-avatar:hover {
  transform: scale(1.12);
  box-shadow: var(--hm-glow-brand-strong);
}

/* ── 通用区块 ── */
.hm-wb-section {
  margin-bottom: 28px;
}

.hm-wb-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.hm-wb-section-header .hm-wb-section-title {
  margin-bottom: 0;
}

.hm-wb-section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--hm-font-primary);
  margin-bottom: 16px;
  letter-spacing: -0.2px;
}

.hm-wb-view-all {
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--hm-brand);
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--hm-radius-full);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-view-all:hover {
  background: var(--hm-brand-bg-light);
  transform: translateX(2px);
}

/* ── 进度环 ── */
.hm-wb-progress-ring-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.hm-wb-ring-text {
  font-size: 11px;
  font-weight: 700;
  color: var(--hm-brand);
}

.hm-wb-ring-progress {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 0 4px rgba(10, 89, 247, 0.3));
}

/* ── 数据概览 ── */
.hm-wb-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}

.hm-wb-stat-card {
  position: relative;
  background: var(--hm-bg-glass);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border-radius: var(--hm-radius-xl);
  padding: 20px 16px;
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  text-align: center;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
}

.hm-wb-stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: var(--hm-radius-xl) var(--hm-radius-xl) 0 0;
  opacity: 0;
  transition: opacity 0.3s;
}

.hm-wb-stat-card:nth-child(1)::before { background: linear-gradient(90deg, #0A59F7, #337BF7); }
.hm-wb-stat-card:nth-child(2)::before { background: linear-gradient(90deg, #ED6F21, #F08C42); }
.hm-wb-stat-card:nth-child(3)::before { background: linear-gradient(90deg, #64BB5C, #7DCC75); }
.hm-wb-stat-card:nth-child(4)::before { background: linear-gradient(90deg, #722ED1, #9254DE); }

.hm-wb-stat-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: var(--hm-glow-brand);
}

.hm-wb-stat-card:hover::before {
  opacity: 1;
}

.hm-wb-stat-card:active {
  transform: translateY(-1px) scale(0.97);
  transition-duration: 0.08s;
}

.hm-wb-stat-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--hm-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-stat-card:hover .hm-wb-stat-icon {
  transform: scale(1.12) rotate(-3deg);
}

.hm-wb-stat-value {
  font-size: 30px;
  font-weight: 700;
  color: var(--hm-font-primary);
  line-height: 1;
  margin-bottom: 6px;
  letter-spacing: -0.5px;
}

.hm-wb-stat-label {
  font-size: 12px;
  color: var(--hm-font-tertiary);
  font-weight: 500;
}

/* ── 追踪条 ── */
.hm-wb-tracker-bar {
  display: flex;
  height: 10px;
  border-radius: var(--hm-radius-full);
  overflow: hidden;
  background: rgba(0, 0, 0, 0.03);
  margin-bottom: 10px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04);
}

.hm-wb-bar-segment {
  min-width: 3px;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-bar-legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--hm-font-fourth);
}

.hm-wb-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: color 0.2s;
}

.hm-wb-legend-item:hover {
  color: var(--hm-font-secondary);
}

.hm-wb-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

/* ── 双栏布局 ── */
.hm-wb-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.hm-wb-two-col .hm-wb-section {
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.hm-wb-two-col .hm-wb-section .hm-wb-chart-card,
.hm-wb-two-col .hm-wb-section .hm-wb-timeline-card {
  flex: 1;
}

/* ── 图表卡片 ── */
.hm-wb-chart-card {
  background: var(--hm-bg-glass);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  padding: 22px;
  min-height: 180px;
  transition: box-shadow 0.3s;
}

.hm-wb-chart-card:hover {
  box-shadow: var(--hm-shadow-layered-hover);
}

.hm-wb-chart {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 120px;
}

.hm-wb-chart-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  height: 100%;
}

.hm-wb-chart-bar-wrap {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.hm-wb-chart-bar {
  width: 28px;
  border-radius: 8px 8px 4px 4px;
  transition: height 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  min-height: 4px;
  position: relative;
}

.hm-wb-chart-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  border-radius: inherit;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, transparent 100%);
  pointer-events: none;
}

.hm-wb-chart-label {
  font-size: 11px;
  color: var(--hm-font-fourth);
  white-space: nowrap;
  font-weight: 500;
}

.hm-wb-chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 140px;
}

.hm-wb-chart-empty p {
  font-size: 13px;
  color: var(--hm-font-fourth);
  margin-top: 8px;
}

/* ── 时间线卡片 ── */
.hm-wb-timeline-card {
  background: var(--hm-bg-glass);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  padding: 22px;
  min-height: 180px;
  transition: box-shadow 0.3s;
}

.hm-wb-timeline-card:hover {
  box-shadow: var(--hm-shadow-layered-hover);
}

.hm-wb-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.hm-wb-timeline-item {
  display: flex;
  align-items: flex-start;
  position: relative;
  padding-bottom: 18px;
}

.hm-wb-timeline-item:last-child {
  padding-bottom: 0;
}

.hm-wb-timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
  position: relative;
  z-index: 1;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.8);
}

.hm-wb-timeline-dot::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid currentColor;
  opacity: 0;
  animation: hm-dot-pulse 2s ease-in-out infinite;
}

@keyframes hm-dot-pulse {
  0%, 100% { opacity: 0; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(1.8); box-shadow: 0 0 12px currentColor; }
}

.hm-wb-timeline-line {
  position: absolute;
  left: 4px;
  top: 16px;
  width: 2px;
  bottom: 0;
  background: linear-gradient(180deg, var(--hm-divider) 0%, transparent 100%);
  border-radius: 1px;
}

.hm-wb-timeline-content {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 14px;
  min-width: 0;
  flex: 1;
  padding: 6px 10px;
  border-radius: var(--hm-radius-md);
  transition: background 0.2s;
}

.hm-wb-timeline-content:hover {
  background: var(--hm-hover-bg);
}

.hm-wb-timeline-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hm-wb-timeline-text {
  font-size: 13px;
  color: var(--hm-font-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
  font-weight: 500;
}

.hm-wb-timeline-time {
  font-size: 11px;
  color: var(--hm-font-fourth);
  flex-shrink: 0;
}

/* ── 功能中心 ── */
.hm-wb-feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.hm-wb-feature-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 24px 14px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  text-align: center;
  overflow: hidden;
}

.hm-wb-feature-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    105deg,
    transparent 40%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 60%
  );
  pointer-events: none;
}

.hm-wb-feature-card:hover .hm-wb-feature-shimmer {
  animation: hm-shimmer-sweep 0.6s ease forwards;
}

@keyframes hm-shimmer-sweep {
  from { left: -100%; }
  to { left: 100%; }
}

.hm-wb-feature-card:hover {
  transform: translateY(-6px) scale(1.03);
  box-shadow: var(--hm-glow-brand);
  border-color: rgba(10, 89, 247, 0.12);
}

.hm-wb-feature-card:active {
  transform: translateY(-2px) scale(0.96);
  transition-duration: 0.08s;
}

.hm-wb-feature-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--hm-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-feature-card:hover .hm-wb-feature-icon {
  transform: scale(1.15) rotate(-5deg);
}

.hm-wb-feature-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-wb-feature-desc {
  font-size: 11px;
  color: var(--hm-font-tertiary);
  line-height: 1.5;
}

/* ── 最近对话 ── */
.hm-wb-history-card {
  background: var(--hm-bg-glass);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  padding: 18px;
}

.hm-wb-conv-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-wb-conv-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--hm-radius-lg);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
}

.hm-wb-conv-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 60%;
  border-radius: 2px;
  background: var(--hm-brand);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-conv-item:hover {
  background: var(--hm-brand-bg-light);
  padding-left: 20px;
}

.hm-wb-conv-item:hover::before {
  transform: translateY(-50%) scaleY(1);
}

.hm-wb-conv-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--hm-radius-md);
  background: linear-gradient(135deg, var(--hm-brand-light) 0%, var(--hm-brand-bg-light) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.hm-wb-conv-item:hover .hm-wb-conv-icon {
  transform: scale(1.08);
}

.hm-wb-conv-info {
  flex: 1;
  min-width: 0;
}

.hm-wb-conv-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-wb-conv-meta {
  font-size: 12px;
  color: var(--hm-font-fourth);
  margin-top: 3px;
}

.hm-wb-conv-time {
  font-size: 12px;
  color: var(--hm-font-fourth);
  flex-shrink: 0;
}

/* ── 骨架屏 ── */
.hm-wb-skeleton {
  margin-bottom: 28px;
}

.hm-skeleton-row {
  display: flex;
  gap: 14px;
}

.hm-skeleton-card {
  flex: 1;
  height: 110px;
  border-radius: var(--hm-radius-xl);
  background: linear-gradient(90deg, rgba(255,255,255,0.5) 25%, rgba(0,0,0,0.03) 50%, rgba(255,255,255,0.5) 75%);
  background-size: 200% 100%;
  animation: hm-skeleton-pulse 1.8s ease-in-out infinite;
}

.hm-skeleton-wide {
  flex: 2;
  height: 180px;
  border-radius: var(--hm-radius-xl);
  background: linear-gradient(90deg, rgba(255,255,255,0.5) 25%, rgba(0,0,0,0.03) 50%, rgba(255,255,255,0.5) 75%);
  background-size: 200% 100%;
  animation: hm-skeleton-pulse 1.8s ease-in-out infinite;
}

.hm-skeleton-narrow {
  flex: 1;
  height: 180px;
  border-radius: var(--hm-radius-xl);
  background: linear-gradient(90deg, rgba(255,255,255,0.5) 25%, rgba(0,0,0,0.03) 50%, rgba(255,255,255,0.5) 75%);
  background-size: 200% 100%;
  animation: hm-skeleton-pulse 1.8s ease-in-out infinite;
}

@keyframes hm-skeleton-pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── 入场动画（鸿蒙 dissolve） ── */
.hm-wb-fade-in {
  animation: hm-wb-fade-in 0.55s var(--hm-spring) both;
}

@keyframes hm-wb-fade-in {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.96);
    filter: blur(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .hm-workbench {
    padding: 16px 12px;
  }
  .hm-wb-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 18px 16px;
    gap: 16px;
  }
  .hm-wb-header-right {
    width: 100%;
    justify-content: space-between;
  }
  .hm-wb-title {
    font-size: 22px;
  }
  .hm-wb-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .hm-wb-two-col {
    grid-template-columns: 1fr;
  }
  .hm-wb-feature-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .hm-wb-feature-card {
    padding: 16px 10px 14px;
  }
  .hm-wb-feature-icon {
    width: 40px;
    height: 40px;
  }
  .hm-wb-quick-actions {
    display: none;
  }
  .hm-wb-header-glow {
    width: 120px;
    height: 120px;
  }
  .hm-wb-stat-card {
    padding: 14px;
  }
  .hm-wb-stat-icon {
    width: 36px;
    height: 36px;
  }
  .hm-wb-stat-value {
    font-size: 20px;
  }
  .hm-wb-conv-item {
    padding: 10px 12px;
  }
  .hm-wb-conv-icon {
    width: 34px;
    height: 34px;
  }
  .hm-wb-chart-card,
  .hm-wb-timeline-card {
    padding: 16px;
  }
  .hm-wb-timeline-text {
    white-space: normal;
    line-height: 1.4;
  }
}

@media (max-width: 480px) {
  .hm-wb-stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .hm-wb-feature-grid {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .hm-wb-feature-desc {
    display: none;
  }
}
</style>
