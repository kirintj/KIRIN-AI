<script setup lang="ts">
import { useInterviewStore } from '@/store/modules/interview-sim'
import { onMounted, ref, watch, nextTick, computed } from 'vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NModal, NForm, NFormItem, NInput, NSelect, NPopconfirm } from 'naive-ui'
import { useMarkdown } from '@/composables/useMarkdown'

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

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

watch(() => store.messages, () => scrollToBottom(), { deep: true })

onMounted(() => {
  store.loadSessions()
})
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-interview-sim">
    <div class="hm-is-sidebar">
      <div class="hm-is-sidebar-header">
        <span class="hm-is-sidebar-title">面试模拟</span>
        <button class="hm-is-new-btn" @click="handleNewSession">
          <TheIcon icon="icon-park-outline:plus" :size="14" />
          新面试
        </button>
      </div>
      <div class="hm-is-stats-row">
        <div class="hm-is-stat">
          <span class="hm-is-stat-val">{{ sessionStats.total }}</span>
          <span class="hm-is-stat-label">总场次</span>
        </div>
        <div class="hm-is-stat">
          <span class="hm-is-stat-val" style="color: #64BB5C">{{ sessionStats.completed }}</span>
          <span class="hm-is-stat-label">已完成</span>
        </div>
        <div class="hm-is-stat">
          <span class="hm-is-stat-val" style="color: var(--hm-brand)">{{ sessionStats.avgScore }}</span>
          <span class="hm-is-stat-label">平均分</span>
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
              {{ session.company || '未指定公司' }} - {{ session.position || '未指定岗位' }}
            </div>
            <div class="hm-is-session-meta">
              <span :class="['hm-is-status', session.status]">
                {{ session.status === 'completed' ? '已完成' : '进行中' }}
              </span>
              <span v-if="session.score" class="hm-is-score">{{ session.score }}分</span>
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
              确定删除该面试记录？
            </NPopconfirm>
          </div>
        </div>
        <div v-if="store.sessions.length === 0" class="hm-is-empty">
          <TheIcon icon="icon-park-outline:people-talk" :size="32" color="var(--hm-font-fourth)" />
          <p>暂无面试记录</p>
          <span @click="handleNewSession">开始模拟面试</span>
        </div>
      </div>
    </div>

    <div class="hm-is-main">
      <div v-if="!store.currentSession" class="hm-is-welcome">
        <div class="hm-is-welcome-icon">
          <TheIcon icon="icon-park-outline:people-talk" :size="48" color="var(--hm-brand)" />
        </div>
        <h2>AI 面试模拟</h2>
        <p>模拟真实面试场景，AI 扮演面试官与你进行多轮对话</p>
        <div class="hm-is-types">
          <div v-for="(label, key) in store.INTERVIEW_TYPES" :key="key" class="hm-is-type-card" @click="setupForm.interview_type = key; showSetupModal = true">
            <span class="hm-is-type-label">{{ label }}</span>
          </div>
        </div>
      </div>

      <template v-else>
        <div class="hm-is-chat-header">
          <div class="hm-is-chat-info">
            <span class="hm-is-chat-company">{{ store.currentSession.company || '未指定公司' }}</span>
            <span class="hm-is-chat-divider">·</span>
            <span class="hm-is-chat-position">{{ store.currentSession.position || '未指定岗位' }}</span>
            <span class="hm-is-chat-type-tag">{{ store.INTERVIEW_TYPES[store.currentSession.interview_type] }}</span>
          </div>
          <div class="hm-is-chat-actions">
            <button
              v-if="store.currentSession.status === 'active'"
              class="hm-is-evaluate-btn"
              @click="handleEvaluate"
              :disabled="store.messages.length < 4 || store.isEvaluating"
            >
              <TheIcon icon="icon-park-outline:score" :size="14" />
              {{ store.isEvaluating ? '评估中...' : '结束并评估' }}
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
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <div v-if="store.currentSession.status === 'active'" class="hm-is-input-area">
          <div class="hm-is-input-box">
            <textarea
              v-model="message"
              class="hm-is-textarea"
              placeholder="输入你的回答..."
              rows="2"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <button
              class="hm-is-send-btn"
              :class="{ active: message.trim() && !store.isLoading }"
              :disabled="!message.trim() || store.isLoading"
              @click="sendMessage"
            >
              <TheIcon icon="icon-park-outline:arrow-up" :size="18" color="#fff" />
            </button>
          </div>
        </div>
        <div v-else class="hm-is-completed-bar">
          <span>面试已结束</span>
          <span v-if="store.currentSession.score" class="hm-is-final-score">得分：{{ store.currentSession.score }}/10</span>
          <button class="hm-is-view-eval" @click="evaluationResult = store.currentSession.evaluation; showEvaluation = true">查看评估</button>
        </div>
      </template>
    </div>

    <NModal v-model:show="showSetupModal" preset="card" title="开始面试模拟" style="width: 440px">
      <NForm label-placement="left" label-width="80">
        <NFormItem label="面试类型">
          <NSelect v-model:value="setupForm.interview_type" :options="interviewTypeOptions" />
        </NFormItem>
        <NFormItem label="目标公司">
          <NInput v-model:value="setupForm.company" placeholder="如 字节跳动（可选）" />
        </NFormItem>
        <NFormItem label="应聘岗位">
          <NInput v-model:value="setupForm.position" placeholder="如 前端开发工程师" />
        </NFormItem>
      </NForm>
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <button class="hm-modal-btn" @click="showSetupModal = false">取消</button>
          <button class="hm-modal-btn primary" @click="handleStartInterview">开始面试</button>
        </div>
      </template>
    </NModal>

    <NModal v-model:show="showEvaluation" preset="card" title="面试评估报告" style="width: 560px">
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
        <button class="hm-modal-btn primary" @click="showEvaluation = false">关闭</button>
      </template>
    </NModal>
  </div>
  </AppPage>
</template>

<style scoped>
.hm-interview-sim {
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
}

.hm-is-sidebar {
  width: 260px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-right: 1px solid var(--hm-border-glass);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.hm-is-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--hm-divider);
}

.hm-is-sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-is-new-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--hm-brand);
  border-radius: var(--hm-radius-full);
  background: transparent;
  color: var(--hm-brand);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-is-new-btn:hover {
  background: var(--hm-brand-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(10, 89, 247, 0.12);
}

.hm-is-stats-row {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--hm-divider);
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
  background: rgba(10, 89, 247, 0.04);
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
  background: rgba(10, 89, 247, 0.1);
  color: var(--hm-brand);
}

.hm-is-status.completed {
  background: rgba(100, 187, 92, 0.1);
  color: #64BB5C;
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
  color: #E84026;
  background: rgba(232, 64, 38, 0.08);
  transform: scale(1.1);
}

.hm-is-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.hm-is-empty p {
  font-size: 13px;
  color: var(--hm-font-fourth);
  margin-top: 8px;
}

.hm-is-empty span {
  font-size: 13px;
  color: var(--hm-brand);
  cursor: pointer;
  margin-top: 4px;
  transition: all 0.25s var(--hm-spring);
}

.hm-is-empty span:hover {
  transform: translateY(-1px);
}

.hm-is-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.hm-is-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}

.hm-is-welcome-icon {
  width: 80px;
  height: 80px;
  border-radius: var(--hm-radius-xl);
  background: var(--hm-brand-light);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: transform 0.35s var(--hm-spring);
}

.hm-is-welcome-icon:hover {
  transform: scale(1.08) rotate(-3deg);
}

.hm-is-welcome h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--hm-font-primary);
  margin-bottom: 8px;
  letter-spacing: -0.3px;
}

.hm-is-welcome p {
  font-size: 14px;
  color: var(--hm-font-tertiary);
  margin-bottom: 28px;
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

.hm-is-chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-bottom: 1px solid var(--hm-border-glass);
  flex-shrink: 0;
}

.hm-is-chat-info {
  display: flex;
  align-items: center;
  gap: 6px;
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
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  color: #fff;
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
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  color: #fff;
  box-shadow: var(--hm-shadow-brand);
}

.hm-is-typing {
  display: flex;
  gap: 4px;
  padding: 14px 18px;
}

.hm-is-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--hm-brand);
  animation: hm-is-bounce 1.2s infinite ease-in-out;
}

.hm-is-typing span:nth-child(2) { animation-delay: 0.15s; }
.hm-is-typing span:nth-child(3) { animation-delay: 0.3s; }

@keyframes hm-is-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.hm-is-input-area {
  padding: 12px 20px 20px;
  flex-shrink: 0;
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
  box-shadow: 0 0 0 3px rgba(10, 89, 247, 0.08);
}

.hm-is-textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  background: transparent;
  font-family: inherit;
  color: var(--hm-font-primary);
}

.hm-is-textarea::placeholder {
  color: var(--hm-font-fourth);
}

.hm-is-send-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--hm-radius-full);
  border: none;
  background: var(--hm-font-fourth);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: not-allowed;
  transition: all 0.3s var(--hm-spring);
  flex-shrink: 0;
}

.hm-is-send-btn.active {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  cursor: pointer;
  box-shadow: var(--hm-shadow-brand);
}

.hm-is-send-btn.active:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35);
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
  background: rgba(0, 0, 0, 0.06);
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
  background: rgba(0, 0, 0, 0.06);
  font-weight: bold;
  font-size: 13px;
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
  .hm-is-sidebar {
    width: 0;
    display: none;
  }
}
</style>
