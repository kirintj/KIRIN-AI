<script setup lang="ts">
import { useInterviewStore } from '@/store/modules/interview-sim'
import { onMounted, ref, watch, nextTick, computed, reactive } from 'vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import LoadingDots from '@/components/common/LoadingDots.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatShortDate } from '@/utils/common/time'
import { NModal, NForm, NFormItem, NInput, NSelect, NPopconfirm, NDrawer, NDrawerContent } from 'naive-ui'
import { useMarkdown } from '@/composables/useMarkdown'
import { useBreakpoints } from '@vueuse/core'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const breakpoints = reactive(useBreakpoints({ sm: 768 }))
const isMobile = breakpoints.smaller('sm')
const mobileDrawerVisible = ref(false)

const store = useInterviewStore()
const { formatMarkdown } = useMarkdown()
const message = ref('')
const msgListRef = ref<HTMLElement | null>(null)
const showSetupModal = ref(false)
const showEvaluation = ref(false)
const evaluationResult = ref<any>(null)

const sessionStats = computed(() => {
  const total = store.sessions.length
  const completed = store.sessions.filter((s: any) => s.status === 'completed').length
  const avgScore = completed > 0
    ? (store.sessions
        .filter((s: any) => s.status === 'completed' && s.score)
        .reduce((sum: number, s: any) => sum + (s.score || 0), 0) / completed).toFixed(1)
    : '0.0'
  return { total, completed, avgScore }
})

const scoreDimensions = computed(() => {
  if (!evaluationResult.value?.dimensions) return []
  return Object.entries(evaluationResult.value.dimensions).map(([key, val]) => ({
    label: key,
    score: val as number,
    maxScore: 10,
    percent: Math.round(((val as number) / 10) * 100),
  }))
})

const setupForm = ref({
  company: '',
  position: '',
  interview_type: 'tech',
})

const interviewTypeOptions = Object.entries(store.INTERVIEW_TYPES).map(([value, label]) => ({
  label,
  value,
}))

const handleStartInterview = async () => {
  if (!setupForm.value.position) return
  await store.createSession(setupForm.value)
  showSetupModal.value = false
  scrollToBottom()
}

const sendMessage = () => {
  if (!message.value.trim() || store.isLoading) return
  store.sendMessage(message.value)
  message.value = ''
  nextTick(scrollToBottom)
}

const handleEvaluate = async () => {
  const result = await store.evaluateCurrentSession()
  if (result) {
    evaluationResult.value = result
    showEvaluation.value = true
  }
}

const handleNewSession = () => {
  store.resetCurrentSession()
  setupForm.value = { company: '', position: '', interview_type: 'tech' }
  showSetupModal.value = true
}

const handleSelectSession = async (sessionId: string) => {
  await store.loadSession(sessionId)
  nextTick(scrollToBottom)
}

const handleDeleteSession = async (sessionId: string) => {
  await store.deleteSession(sessionId)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (msgListRef.value) {
      msgListRef.value.scrollTop = msgListRef.value.scrollHeight
    }
  })
}

watch(() => store.messages, () => scrollToBottom(), { deep: true })

onMounted(() => {
  store.loadSessions()
})
</script>

<template>
  <div class="hm-sidebar-layout">
    <template v-if="isMobile">
      <n-drawer v-model:show="mobileDrawerVisible" :width="280" placement="left" :auto-focus="false">
        <n-drawer-content :native-scrollbar="false" body-content-style="padding: 0;" :title="t('views.interview_sim.page_title')">
          <div class="hm-is-sidebar-drawer">
            <div class="hm-is-stats-row">
              <div class="hm-is-stat">
                <span class="hm-is-stat-val">{{ sessionStats.total }}</span>
                <span class="hm-is-stat-label">{{ t('views.interview_sim.stat_total') }}</span>
              </div>
              <div class="hm-is-stat">
                <span class="hm-is-stat-val" style="color: #64BB5C">{{ sessionStats.completed }}</span>
                <span class="hm-is-stat-label">{{ t('views.interview_sim.stat_completed') }}</span>
              </div>
              <div class="hm-is-stat">
                <span class="hm-is-stat-val" style="color: var(--hm-brand)">{{ sessionStats.avgScore }}</span>
                <span class="hm-is-stat-label">{{ t('views.interview_sim.stat_avg_score') }}</span>
              </div>
            </div>
            <div class="hm-is-session-list">
              <div
                v-for="session in store.sessions"
                :key="session.id"
                :class="['hm-is-session-item', { active: session.id === store.currentSession?.id }]"
                @click="handleSelectSession(session.id); mobileDrawerVisible = false"
              >
                <div class="hm-is-session-info">
                  <div class="hm-is-session-title">
                    {{ session.company || t('views.interview_sim.unspecified_company') }} - {{ session.position || t('views.interview_sim.unspecified_position') }}
                  </div>
                  <div class="hm-is-session-meta">
                    <span :class="['hm-is-status', session.status]">
                      {{ session.status === 'completed' ? t('views.interview_sim.status_completed') : t('views.interview_sim.status_active') }}
                    </span>
                    <span v-if="session.score" class="hm-is-score">{{ session.score }}{{ t('views.interview_sim.score_suffix') }}</span>
                    <span class="hm-is-type">{{ store.INTERVIEW_TYPES[session.interview_type] || session.interview_type }}</span>
                  </div>
                </div>
                <div class="hm-is-session-actions" @click.stop>
                  <NPopconfirm @positive-click="handleDeleteSession(session.id)">
                    <template #trigger>
                      <button class="hm-is-session-action">
                        <TheIcon icon="icon-park-outline:delete" :size="12" />
                      </button>
                    </template>
                    {{ t('views.interview_sim.confirm_delete') }}
                  </NPopconfirm>
                </div>
              </div>
              <EmptyState
                v-if="store.sessions.length === 0"
                icon="icon-park-outline:people-talk"
                :title="t('views.interview_sim.empty_no_records')"
              >
                <span class="hm-is-empty-action" @click="handleNewSession">{{ t('views.interview_sim.btn_start') }}</span>
              </EmptyState>
            </div>
          </div>
        </n-drawer-content>
      </n-drawer>
    </template>
    <template v-else>
    <div class="hm-sidebar">
      <div class="hm-sidebar-header">
        <span class="hm-sidebar-title">{{ t('views.interview_sim.page_title') }}</span>
        <button class="hm-sidebar-new-btn" @click="handleNewSession">
          <TheIcon icon="icon-park-outline:plus" :size="14" />
          {{ t('views.interview_sim.btn_new') }}
        </button>
      </div>
      <div class="hm-is-stats-row">
        <div class="hm-is-stat">
          <span class="hm-is-stat-val">{{ sessionStats.total }}</span>
          <span class="hm-is-stat-label">{{ t('views.interview_sim.stat_total') }}</span>
        </div>
        <div class="hm-is-stat">
          <span class="hm-is-stat-val" style="color: #64BB5C">{{ sessionStats.completed }}</span>
          <span class="hm-is-stat-label">{{ t('views.interview_sim.stat_completed') }}</span>
        </div>
        <div class="hm-is-stat">
          <span class="hm-is-stat-val" style="color: var(--hm-brand)">{{ sessionStats.avgScore }}</span>
          <span class="hm-is-stat-label">{{ t('views.interview_sim.stat_avg_score') }}</span>
        </div>
      </div>
      <div class="hm-is-session-list">
        <div
          v-for="session in store.sessions"
          :key="session.id"
          :class="['hm-is-session-item', { active: session.id === store.currentSession?.id }]"
          @click="handleSelectSession(session.id)"
        >
          <div class="hm-is-session-info">
            <div class="hm-is-session-title">
              {{ session.company || t('views.interview_sim.unspecified_company') }} - {{ session.position || t('views.interview_sim.unspecified_position') }}
            </div>
            <div class="hm-is-session-meta">
              <span :class="['hm-is-status', session.status]">
                {{ session.status === 'completed' ? t('views.interview_sim.status_completed') : t('views.interview_sim.status_active') }}
              </span>
              <span v-if="session.score" class="hm-is-score">{{ session.score }}{{ t('views.interview_sim.score_suffix') }}</span>
              <span class="hm-is-type">{{ store.INTERVIEW_TYPES[session.interview_type] || session.interview_type }}</span>
            </div>
          </div>
          <div class="hm-is-session-actions" @click.stop>
            <NPopconfirm @positive-click="handleDeleteSession(session.id)">
              <template #trigger>
                <button class="hm-is-session-action">
                  <TheIcon icon="icon-park-outline:delete" :size="12" />
                </button>
              </template>
              {{ t('views.interview_sim.confirm_delete') }}
            </NPopconfirm>
          </div>
        </div>
        <EmptyState
          v-if="store.sessions.length === 0"
          icon="icon-park-outline:people-talk"
          :title="t('views.interview_sim.empty_no_records')"
        >
          <span class="hm-is-empty-action" @click="handleNewSession">{{ t('views.interview_sim.btn_start') }}</span>
        </EmptyState>
      </div>
    </div>
    </template>

    <div class="hm-is-main">
      <EmptyState
        v-if="!store.currentSession"
        icon="icon-park-outline:people-talk"
        :title="t('views.interview_sim.empty_title')"
        :description="t('views.interview_sim.empty_desc')"
      >
        <div class="hm-is-types">
          <div v-for="(label, key) in store.INTERVIEW_TYPES" :key="key" class="hm-is-type-card" @click="setupForm.interview_type = key; showSetupModal = true">
            <span class="hm-is-type-label">{{ label }}</span>
          </div>
        </div>
      </EmptyState>

      <template v-else>
        <div class="hm-toolbar">
          <div class="hm-toolbar-left">
            <button v-if="isMobile" class="hm-is-mobile-btn" @click="mobileDrawerVisible = true">
              <TheIcon icon="icon-park-outline:people-talk" :size="16" />
            </button>
            <span class="hm-is-chat-company">{{ store.currentSession.company || t('views.interview_sim.unspecified_company') }}</span>
            <span class="hm-is-chat-divider">·</span>
            <span class="hm-is-chat-position">{{ store.currentSession.position || t('views.interview_sim.unspecified_position') }}</span>
            <span class="hm-is-chat-type-tag">{{ store.INTERVIEW_TYPES[store.currentSession.interview_type] }}</span>
          </div>
          <div class="hm-toolbar-right">
            <button
              v-if="store.currentSession.status === 'active'"
              class="hm-is-evaluate-btn"
              @click="handleEvaluate"
              :disabled="store.messages.length < 4 || store.isEvaluating"
            >
              <TheIcon icon="icon-park-outline:score" :size="14" />
              {{ store.isEvaluating ? t('views.interview_sim.btn_evaluating') : t('views.interview_sim.btn_evaluate') }}
            </button>
          </div>
        </div>

        <div ref="msgListRef" class="hm-is-messages">
          <div
            v-for="(msg, index) in store.messages"
            :key="index"
            :class="['hm-is-msg', msg.role]"
          >
            <div v-if="msg.role === 'assistant'" class="hm-is-msg-avatar interviewer">
              <TheIcon icon="icon-park-outline:people-talk" :size="16" color="#fff" />
            </div>
            <div class="hm-is-msg-bubble" v-html="msg.role === 'assistant' ? formatMarkdown(msg.content) : msg.content"></div>
          </div>
          <div v-if="store.isLoading" class="hm-is-msg assistant">
            <div class="hm-is-msg-avatar interviewer">
              <TheIcon icon="icon-park-outline:people-talk" :size="16" color="#fff" />
            </div>
            <div class="hm-is-msg-bubble hm-is-typing">
              <LoadingDots />
            </div>
          </div>
        </div>

        <div v-if="store.currentSession.status === 'active'" class="hm-input-area">
          <div class="hm-is-input-box">
            <textarea
              v-model="message"
              class="hm-textarea"
              :placeholder="t('views.interview_sim.input_placeholder')"
              rows="2"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <button
              class="hm-send-btn"
              :class="{ active: message.trim() && !store.isLoading }"
              :disabled="!message.trim() || store.isLoading"
              @click="sendMessage"
            >
              <TheIcon icon="icon-park-outline:arrow-up" :size="18" color="#fff" />
            </button>
          </div>
        </div>
        <div v-else class="hm-is-completed-bar">
          <span>{{ t('views.interview_sim.interview_ended') }}</span>
          <span v-if="store.currentSession.score" class="hm-is-final-score">{{ t('views.interview_sim.final_score', { score: store.currentSession.score }) }}</span>
          <button class="hm-is-view-eval" @click="evaluationResult = store.currentSession.evaluation; showEvaluation = true">{{ t('views.interview_sim.btn_view_eval') }}</button>
        </div>
      </template>
    </div>

    <NModal v-model:show="showSetupModal" preset="card" :title="t('views.interview_sim.modal_title')" style="width: 440px">
      <NForm label-placement="left" label-width="80">
        <NFormItem :label="t('views.interview_sim.form_type')">
          <NSelect v-model:value="setupForm.interview_type" :options="interviewTypeOptions" />
        </NFormItem>
        <NFormItem :label="t('views.interview_sim.form_company')">
          <NInput v-model:value="setupForm.company" :placeholder="t('views.interview_sim.form_company_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.interview_sim.form_position')">
          <NInput v-model:value="setupForm.position" :placeholder="t('views.interview_sim.form_position_placeholder')" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <button class="hm-modal-btn" @click="showSetupModal = false">{{ t('views.interview_sim.btn_cancel') }}</button>
          <button class="hm-modal-btn primary" @click="handleStartInterview">{{ t('views.interview_sim.btn_start_interview') }}</button>
        </div>
      </template>
    </NModal>

    <NModal v-model:show="showEvaluation" preset="card" :title="t('views.interview_sim.eval_title')" style="width: 560px">
      <div v-if="evaluationResult" class="hm-is-eval-content">
        <div v-if="evaluationResult.score" class="hm-is-eval-score">
          <span class="hm-is-eval-score-num">{{ evaluationResult.score }}</span>
          <span class="hm-is-eval-score-max">/10</span>
        </div>
        <div v-if="scoreDimensions.length" class="hm-is-eval-dimensions">
          <div v-for="dim in scoreDimensions" :key="dim.label" class="hm-is-dim-item">
            <div class="hm-is-dim-header">
              <span class="hm-is-dim-label">{{ dim.label }}</span>
              <span class="hm-is-dim-score">{{ dim.score }}/{{ dim.maxScore }}</span>
            </div>
            <div class="hm-is-dim-track">
              <div class="hm-is-dim-fill" :style="{ width: dim.percent + '%' }"></div>
            </div>
          </div>
        </div>
        <div class="hm-is-eval-text md-bubble" v-html="formatMarkdown(evaluationResult.evaluation_text || '')"></div>
      </div>
      <template #footer>
        <button class="hm-modal-btn primary" @click="showEvaluation = false">{{ t('views.interview_sim.btn_close') }}</button>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.hm-is-sidebar-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.hm-is-stats-row {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--hm-border-glass);
}

.hm-is-stat {
  flex: 1;
  text-align: center;
  padding: 8px 4px;
  background: var(--hm-bg-container-secondary);
  border-radius: var(--hm-radius-md);
}

.hm-is-stat-val {
  font-size: 18px;
  font-weight: 700;
  color: var(--hm-font-primary);
  display: block;
  letter-spacing: -0.3px;
}

.hm-is-stat-label {
  font-size: 10px;
  color: var(--hm-font-fourth);
  font-weight: 500;
}

.hm-is-session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.hm-is-session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--hm-radius-md);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
}

.hm-is-session-item:hover {
  background: var(--hm-brand-bg-light);
  transform: translateX(2px);
}

.hm-is-session-item.active {
  background: var(--hm-brand-light);
}

.hm-is-session-info {
  flex: 1;
  min-width: 0;
}

.hm-is-session-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-is-session-meta {
  display: flex;
  gap: 6px;
  margin-top: 3px;
  font-size: 11px;
}

.hm-is-status {
  padding: 1px 6px;
  border-radius: var(--hm-radius-full);
  font-size: 10px;
}

.hm-is-status.active {
  background: var(--hm-brand-bg-light);
  color: var(--hm-brand);
}

.hm-is-status.completed {
  background: rgba(100, 187, 92, 0.1);
  color: var(--hm-success);
}

.hm-is-score {
  color: var(--hm-brand);
  font-weight: 600;
}

.hm-is-type {
  color: var(--hm-font-fourth);
}

.hm-is-session-actions {
  display: none;
}

.hm-is-session-item:hover .hm-is-session-actions {
  display: flex;
}

.hm-is-session-action {
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

.hm-is-session-action:hover {
  color: var(--hm-error);
  background: var(--hm-danger-hover-bg);
  transform: scale(1.1);
}

.hm-is-empty-action {
  font-size: 13px;
  color: var(--hm-brand);
  cursor: pointer;
  margin-top: 4px;
  transition: all 0.25s var(--hm-spring);
}

.hm-is-empty-action:hover {
  transform: translateY(-1px);
}

.hm-is-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.hm-is-types {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.hm-is-type-card {
  padding: 12px 24px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-is-type-card:hover {
  border-color: var(--hm-brand);
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-3px);
}

.hm-is-type-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
}

.hm-is-chat-company {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-is-chat-divider {
  color: var(--hm-font-fourth);
}

.hm-is-chat-position {
  font-size: 14px;
  color: var(--hm-font-secondary);
}

.hm-is-chat-type-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--hm-radius-full);
  background: var(--hm-brand-light);
  color: var(--hm-brand);
  font-weight: 500;
}

.hm-is-evaluate-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 16px;
  border: 1px solid var(--hm-brand);
  border-radius: var(--hm-radius-full);
  background: transparent;
  color: var(--hm-brand);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-is-evaluate-btn:hover:not(:disabled) {
  background: var(--hm-brand-gradient);
  color: var(--hm-font-on-brand);
  border-color: transparent;
  box-shadow: var(--hm-shadow-brand);
  transform: translateY(-1px);
}

.hm-is-evaluate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hm-is-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hm-is-msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  animation: hm-is-msg-in 0.35s var(--hm-spring);
}

@keyframes hm-is-msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.hm-is-msg.user {
  justify-content: flex-end;
}

.hm-is-msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--hm-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hm-is-msg-avatar.interviewer {
  background: linear-gradient(135deg, #722ED1, #9254DE);
  box-shadow: 0 2px 8px rgba(114, 46, 209, 0.25);
}

.hm-is-msg-bubble {
  padding: 10px 14px;
  border-radius: var(--hm-radius-lg);
  font-size: 14px;
  line-height: 1.6;
  max-width: 75%;
  word-break: break-word;
}

.assistant .hm-is-msg-bubble {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  color: var(--hm-font-primary);
}

.user .hm-is-msg-bubble {
  background: var(--hm-brand-gradient);
  color: var(--hm-font-on-brand);
  box-shadow: var(--hm-shadow-brand);
}

.hm-is-typing {
  padding: 4px 8px;
}

.hm-is-input-box {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  padding: 10px 14px;
  transition: all 0.3s var(--hm-spring);
}

.hm-is-input-box:focus-within {
  border-color: var(--hm-brand);
  box-shadow: var(--hm-focus-ring);
}

.hm-is-completed-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-top: 1px solid var(--hm-border-glass);
  font-size: 13px;
  color: var(--hm-font-tertiary);
}

.hm-is-final-score {
  font-weight: 600;
  color: var(--hm-brand);
}

.hm-is-view-eval {
  padding: 5px 14px;
  border: 1px solid var(--hm-brand);
  border-radius: var(--hm-radius-full);
  background: transparent;
  color: var(--hm-brand);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-is-view-eval:hover {
  background: var(--hm-brand-light);
  transform: translateY(-1px);
}

.hm-is-eval-content {
  text-align: center;
}

.hm-is-eval-score {
  margin-bottom: 16px;
}

.hm-is-eval-score-num {
  font-size: 48px;
  font-weight: 700;
  color: var(--hm-brand);
  letter-spacing: -0.5px;
}

.hm-is-eval-score-max {
  font-size: 20px;
  color: var(--hm-font-fourth);
}

.hm-is-eval-text {
  text-align: left;
  font-size: 14px;
  line-height: 1.8;
  color: var(--hm-font-primary);
}

.hm-is-eval-dimensions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 16px 0;
  padding: 16px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-lg);
  border: 1px solid var(--hm-border-glass);
}

.hm-is-dim-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-is-dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hm-is-dim-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-primary);
}

.hm-is-dim-score {
  font-size: 12px;
  color: var(--hm-brand);
  font-weight: 600;
}

.hm-is-dim-track {
  height: 6px;
  border-radius: 3px;
  background: var(--hm-pressed-bg);
  overflow: hidden;
}

.hm-is-dim-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--hm-brand), #337BF7);
  transition: width 0.8s var(--hm-spring);
}

.assistant .hm-is-msg-bubble :not(pre) > code {
  padding: 2px 6px;
  margin: 0 4px;
  border-radius: 4px;
  background: var(--hm-pressed-bg);
  font-weight: bold;
  font-size: 13px;
}

@media (max-width: 768px) {
  .hm-is-mobile-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: 1px solid var(--hm-border);
    border-radius: var(--hm-radius-sm);
    background: transparent;
    color: var(--hm-font-secondary);
    cursor: pointer;
    transition: all 0.25s var(--hm-spring);
    flex-shrink: 0;
  }
  .hm-is-mobile-btn:hover {
    border-color: var(--hm-brand);
    color: var(--hm-brand);
  }
  .hm-toolbar {
    padding: 10px 12px;
  }
  .hm-toolbar-left {
    gap: 4px;
    min-width: 0;
    flex: 1;
  }
  .hm-is-chat-company,
  .hm-is-chat-position {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .hm-is-chat-divider {
    display: none;
  }
  .hm-is-chat-type-tag {
    display: none;
  }
  .hm-is-types {
    gap: 8px;
  }
  .hm-is-type-card {
    padding: 10px 16px;
  }
  .hm-input-area {
    padding: 8px 12px;
  }
  .hm-is-evaluate-btn {
    font-size: 11px;
    padding: 4px 10px;
  }
}

@media (max-width: 480px) {
  .hm-is-type-card {
    padding: 8px 12px;
  }
  .hm-is-type-label {
    font-size: 13px;
  }
}
</style>
