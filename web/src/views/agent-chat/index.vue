<script setup lang="ts">
import { useAgentChatStore } from '@/store/modules/agent-chat'
import { onMounted, watch, ref } from 'vue'
import { useMarkdown } from '@/composables/useMarkdown'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NPopconfirm, NInput } from 'naive-ui'

const agentStore = useAgentChatStore()
const message = ref('')
const { formatMessage, scrollToBottom } = useMarkdown()

const sidebarCollapsed = ref(false)
const renamingId = ref<string | null>(null)
const renameValue = ref('')
const copiedIndex = ref<number | null>(null)
const feedbackMap = ref<Record<number, 'like' | 'dislike'>>({})

const sendMessage = () => {
  if (!message.value.trim() || agentStore.isLoading) return
  if (!agentStore.currentConversationId) {
    agentStore.createConversation().then(() => {
      agentStore.sendMessage(message.value)
      message.value = ''
    })
    return
  }
  agentStore.sendMessage(message.value)
  message.value = ''
}

const quickSend = (text: string) => {
  message.value = text
  sendMessage()
}

const handleNewConversation = () => {
  agentStore.createConversation()
}

const handleSwitchConversation = (convId: string) => {
  agentStore.switchConversation(convId)
}

const handleDeleteConversation = async (convId: string) => {
  await agentStore.deleteConversation(convId)
}

const startRename = (convId: string, currentTitle: string) => {
  renamingId.value = convId
  renameValue.value = currentTitle
}

const confirmRename = async () => {
  if (renamingId.value && renameValue.value.trim()) {
    await agentStore.renameConversation(renamingId.value, renameValue.value.trim())
  }
  renamingId.value = null
}

const cancelRename = () => {
  renamingId.value = null
}

const handleClearMemory = async () => {
  await agentStore.clearMemory()
  if (agentStore.currentConversationId) {
    await agentStore.deleteConversation(agentStore.currentConversationId)
  }
}

const copyMessage = async (content: string, index: number) => {
  try {
    await navigator.clipboard.writeText(content)
    copiedIndex.value = index
    setTimeout(() => { copiedIndex.value = null }, 1500)
  } catch {
    window.$message?.error('复制失败')
  }
}

const regenerateMessage = (index: number) => {
  if (agentStore.isLoading) return
  agentStore.regenerateMessage(index)
}

const toggleFeedback = (index: number, type: 'like' | 'dislike') => {
  feedbackMap.value[index] = feedbackMap.value[index] === type ? undefined as any : type
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const formatMsgTime = (dateStr: string | null) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const shouldShowTime = (messages: any[], index: number) => {
  if (index === 0) return true
  const curr = messages[index].timestamp
  const prev = messages[index - 1].timestamp
  if (!curr || !prev) return false
  return new Date(curr).getTime() - new Date(prev).getTime() > 5 * 60 * 1000
}

const quickCommands = [
  { label: '面试准备', icon: 'icon-park-outline:people-talk', text: '帮我准备字节跳动前端开发的面试', color: '#0A59F7' },
  { label: '薪资谈判', icon: 'icon-park-outline:finance', text: '北京互联网行业前端开发3年经验的薪资谈判建议', color: '#ED6F21' },
  { label: '求职攻略', icon: 'icon-park-outline:map', text: '跨行业跳槽求职攻略', color: '#722ED1' },
  { label: '创建待办', icon: 'icon-park-outline:todo', text: '帮我创建一个待办：明天下午3点准备面试', color: '#64BB5C' },
]

onMounted(async () => {
  await agentStore.loadConversations()
  if (agentStore.conversations.length > 0) {
    await agentStore.switchConversation(agentStore.conversations[0].id)
  }
  scrollToBottom('.hm-msg-list')
})

watch(() => agentStore.messages, () => scrollToBottom('.hm-msg-list'), { deep: true })
</script>

<template>
  <div class="hm-chat-layout">
    <div :class="['hm-sidebar', { collapsed: sidebarCollapsed }]">
      <div :class="['hm-sidebar-header', { collapsed: sidebarCollapsed }]">
        <span v-if="!sidebarCollapsed" class="hm-sidebar-title">对话</span>
        <button v-if="!sidebarCollapsed" class="hm-sidebar-new" @click="handleNewConversation">
          <TheIcon icon="icon-park-outline:plus" :size="16" />
        </button>
        <button class="hm-sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <TheIcon :icon="sidebarCollapsed ? 'icon-park-outline:right' : 'icon-park-outline:left'" :size="14" />
        </button>
      </div>

      <div v-if="!sidebarCollapsed" class="hm-sidebar-search">
        <div class="hm-search-box">
          <TheIcon icon="icon-park-outline:search" :size="14" color="var(--hm-font-fourth)" />
          <input
            v-model="agentStore.searchKeyword"
            class="hm-search-input"
            placeholder="搜索对话..."
          />
          <button
            v-if="agentStore.searchKeyword"
            class="hm-search-clear"
            @click="agentStore.searchKeyword = ''"
          >
            <TheIcon icon="icon-park-outline:close" :size="12" />
          </button>
        </div>
      </div>

      <div v-if="!sidebarCollapsed" class="hm-sidebar-list">
        <template v-for="group in agentStore.groupedConversations" :key="group.label">
          <div class="hm-sidebar-group-label">{{ group.label }}</div>
          <div
            v-for="conv in group.items"
            :key="conv.id"
            :class="['hm-sidebar-item', { active: conv.id === agentStore.currentConversationId }]"
            @click="handleSwitchConversation(conv.id)"
          >
            <TheIcon icon="icon-park-outline:chat" :size="16" class="hm-conv-icon" />
            <div v-if="renamingId === conv.id" class="hm-conv-rename" @click.stop>
              <NInput
                v-model:value="renameValue"
                size="tiny"
                placeholder="输入新名称"
                @keyup.enter="confirmRename"
                @keyup.escape="cancelRename"
                @blur="confirmRename"
                autofocus
              />
            </div>
            <div v-else class="hm-conv-info">
              <div class="hm-conv-title">{{ conv.title || '新对话' }}</div>
              <div class="hm-conv-meta">{{ conv.message_count || 0 }} 条消息 · {{ formatTime(conv.updated_at) }}</div>
            </div>
            <div class="hm-conv-actions" @click.stop>
              <button class="hm-conv-action" @click="startRename(conv.id, conv.title)">
                <TheIcon icon="icon-park-outline:edit" :size="12" />
              </button>
              <NPopconfirm @positive-click="handleDeleteConversation(conv.id)">
                <template #trigger>
                  <button class="hm-conv-action danger">
                    <TheIcon icon="icon-park-outline:delete" :size="12" />
                  </button>
                </template>
                确定删除该对话？
              </NPopconfirm>
            </div>
          </div>
        </template>

        <div v-if="agentStore.conversations.length === 0" class="hm-sidebar-empty">
          <TheIcon icon="icon-park-outline:chat" :size="32" color="var(--hm-font-fourth)" />
          <p>暂无对话</p>
        </div>

        <div v-if="agentStore.conversations.length > 0 && agentStore.filteredConversations.length === 0" class="hm-sidebar-empty">
          <TheIcon icon="icon-park-outline:search" :size="32" color="var(--hm-font-fourth)" />
          <p>未找到匹配的对话</p>
        </div>
      </div>
    </div>

    <div class="hm-chat-page">
      <div class="hm-chat-toolbar">
        <div class="hm-chat-toolbar-left">
          <span class="hm-chat-title">AI Agent</span>
          <span class="hm-chat-badge">智能对话</span>
        </div>
        <div class="hm-chat-toolbar-right">
          <button
            class="hm-toolbar-chip"
            :class="{ active: agentStore.useLangGraph }"
            @click="agentStore.useLangGraph = !agentStore.useLangGraph"
          >
            <TheIcon icon="icon-park-outline:graph" :size="14" />
            {{ agentStore.useLangGraph ? 'LangGraph' : '经典' }}
          </button>
          <button
            class="hm-toolbar-chip"
            :class="{ active: agentStore.useLlmRouter }"
            @click="agentStore.useLlmRouter = !agentStore.useLlmRouter"
          >
            <TheIcon icon="icon-park-outline:brain" :size="14" />
            LLM 路由
          </button>
          <button class="hm-toolbar-chip danger" @click="handleClearMemory">
            <TheIcon icon="icon-park-outline:delete" :size="14" />
            清空
          </button>
        </div>
      </div>

      <div class="hm-chat-body">
        <div class="hm-msg-list">
          <div v-if="agentStore.messages.length === 0" class="hm-chat-empty">
            <div class="hm-empty-icon">
              <TheIcon icon="icon-park-outline:robot" :size="48" color="var(--hm-brand)" />
            </div>
            <p class="hm-empty-title">开始与 AI Agent 对话</p>
            <p class="hm-empty-desc">支持知识问答、面试准备、薪资谈判、求职攻略、待办创建</p>
            <div class="hm-quick-cmds">
              <button
                v-for="cmd in quickCommands"
                :key="cmd.label"
                class="hm-quick-btn"
                @click="quickSend(cmd.text)"
              >
                <div class="hm-quick-icon" :style="{ background: cmd.color + '14' }">
                  <TheIcon :icon="cmd.icon" :size="16" :color="cmd.color" />
                </div>
                <span>{{ cmd.label }}</span>
              </button>
            </div>
          </div>

          <template v-for="(item, index) in agentStore.messages" :key="index">
            <div v-if="shouldShowTime(agentStore.messages, index)" class="hm-msg-time-divider">
              {{ formatMsgTime(item.timestamp) }}
            </div>
            <div :class="['hm-msg-item', item.role]">
              <div v-if="item.role === 'assistant'" class="hm-msg-avatar">
                <TheIcon icon="icon-park-outline:robot" :size="18" color="var(--hm-brand)" />
              </div>
              <div class="hm-msg-content">
                <div v-html="formatMessage(item.content, item.role)" class="hm-msg-bubble md-bubble"></div>
                <div v-if="item.role === 'assistant'" class="hm-msg-actions">
                  <button
                    class="hm-msg-action"
                    @click="copyMessage(item.content, index)"
                  >
                    <TheIcon
                      :icon="copiedIndex === index ? 'icon-park-outline:success' : 'icon-park-outline:copy'"
                      :size="12"
                      :color="copiedIndex === index ? '#64BB5C' : 'var(--hm-font-fourth)'"
                    />
                    {{ copiedIndex === index ? '已复制' : '复制' }}
                  </button>
                  <button
                    class="hm-msg-action"
                    @click="regenerateMessage(index)"
                    :disabled="agentStore.isLoading"
                  >
                    <TheIcon icon="icon-park-outline:refresh" :size="12" color="var(--hm-font-fourth)" />
                    重新生成
                  </button>
                  <button
                    :class="['hm-msg-action', { active: feedbackMap[index] === 'like' }]"
                    @click="toggleFeedback(index, 'like')"
                  >
                    <TheIcon
                      icon="icon-park-outline:like"
                      :size="12"
                      :color="feedbackMap[index] === 'like' ? '#0A59F7' : 'var(--hm-font-fourth)'"
                    />
                  </button>
                  <button
                    :class="['hm-msg-action', { active: feedbackMap[index] === 'dislike' }]"
                    @click="toggleFeedback(index, 'dislike')"
                  >
                    <TheIcon
                      icon="icon-park-outline:dislike"
                      :size="12"
                      :color="feedbackMap[index] === 'dislike' ? '#E84026' : 'var(--hm-font-fourth)'"
                    />
                  </button>
                </div>
              </div>
            </div>
          </template>

          <div v-if="agentStore.isLoading" class="hm-msg-item assistant">
            <div class="hm-msg-avatar">
              <TheIcon icon="icon-park-outline:robot" :size="18" color="var(--hm-brand)" />
            </div>
            <div class="hm-msg-bubble hm-msg-loading">
              <div class="hm-dots">
                <span></span><span></span><span></span>
              </div>
              <span class="hm-loading-text">思考中</span>
              <div class="hm-loading-pulse"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="hm-chat-input-area">
        <div class="hm-input-box">
          <textarea
            v-model="message"
            class="hm-textarea"
            placeholder="输入消息，Agent 自动识别意图..."
            rows="2"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="hm-input-actions">
            <div class="hm-input-chips">
              <button class="hm-mini-chip" @click="quickSend('帮我准备面试')">面试</button>
              <button class="hm-mini-chip" @click="quickSend('薪资谈判建议')">薪资</button>
              <button class="hm-mini-chip" @click="quickSend('求职攻略')">攻略</button>
              <button class="hm-mini-chip" @click="quickSend('帮我创建一个待办')">待办</button>
            </div>
            <button
              class="hm-send-btn"
              :class="{ active: message.trim() && !agentStore.isLoading }"
              :disabled="!message.trim() || agentStore.isLoading"
              @click="sendMessage"
            >
              <TheIcon icon="icon-park-outline:arrow-up" :size="18" color="#fff" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hm-chat-layout {
  height: 100%;
  display: flex;
  background: var(--hm-bg-primary);
  overflow: hidden;
}

.hm-sidebar {
  width: 260px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-right: 1px solid var(--hm-border-glass);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s var(--hm-spring);
  overflow: hidden;
}

.hm-sidebar.collapsed {
  width: 48px;
}

.hm-sidebar-header {
  display: flex;
  align-items: center;
  padding: 12px;
  gap: 8px;
  border-bottom: 1px solid var(--hm-divider);
  flex-shrink: 0;
}

.hm-sidebar-header.collapsed {
  justify-content: center;
  padding: 12px 0;
}

.hm-sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
  flex: 1;
}

.hm-sidebar-new {
  width: 28px;
  height: 28px;
  border-radius: var(--hm-radius-sm);
  border: 1px solid var(--hm-border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-secondary);
  transition: all 0.3s var(--hm-spring);
  flex-shrink: 0;
}

.hm-sidebar-new:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  background: var(--hm-brand-light);
  transform: scale(1.08);
}

.hm-sidebar-toggle {
  width: 28px;
  height: 28px;
  border-radius: var(--hm-radius-sm);
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-fourth);
  transition: all 0.25s var(--hm-spring);
  flex-shrink: 0;
}

.hm-sidebar-toggle:hover {
  color: var(--hm-font-secondary);
  background: rgba(0, 0, 0, 0.04);
  transform: scale(1.08);
}

.hm-sidebar-search {
  padding: 8px 12px;
  flex-shrink: 0;
}

.hm-search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
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
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 12px;
  color: var(--hm-font-primary);
  font-family: inherit;
}

.hm-search-input::placeholder {
  color: var(--hm-font-fourth);
}

.hm-search-clear {
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-fourth);
  transition: all 0.25s var(--hm-spring);
}

.hm-search-clear:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--hm-font-primary);
  transform: scale(1.1);
}

.hm-sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px 8px;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.hm-sidebar-list::-webkit-scrollbar { display: none; }

.hm-sidebar-group-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--hm-font-fourth);
  padding: 10px 12px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hm-sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--hm-radius-md);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
  position: relative;
}

.hm-sidebar-item:hover {
  background: rgba(10, 89, 247, 0.04);
  transform: translateX(2px);
}

.hm-sidebar-item.active {
  background: var(--hm-brand-light);
}

.hm-conv-icon {
  flex-shrink: 0;
  color: var(--hm-font-tertiary);
  transition: transform 0.3s var(--hm-spring);
}

.hm-sidebar-item:hover .hm-conv-icon {
  transform: scale(1.1);
}

.hm-sidebar-item.active .hm-conv-icon {
  color: var(--hm-brand);
}

.hm-conv-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.hm-conv-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-conv-meta {
  font-size: 11px;
  color: var(--hm-font-fourth);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-conv-rename {
  flex: 1;
  min-width: 0;
}

.hm-conv-actions {
  display: none;
  gap: 2px;
  flex-shrink: 0;
}

.hm-sidebar-item:hover .hm-conv-actions {
  display: flex;
}

.hm-conv-action {
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

.hm-conv-action:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--hm-font-primary);
  transform: scale(1.1);
}

.hm-conv-action.danger:hover {
  background: rgba(232, 64, 38, 0.08);
  color: #E84026;
}

.hm-sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.hm-sidebar-empty p {
  font-size: 13px;
  color: var(--hm-font-fourth);
  margin-top: 8px;
}

.hm-chat-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--hm-bg-primary);
  overflow: hidden;
  min-width: 0;
}

.hm-chat-toolbar {
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

.hm-chat-toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hm-chat-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--hm-font-primary);
  letter-spacing: -0.2px;
}

.hm-chat-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--hm-radius-full);
  background: var(--hm-brand-light);
  color: var(--hm-brand);
  font-weight: 500;
}

.hm-chat-toolbar-right {
  display: flex;
  gap: 6px;
}

.hm-toolbar-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  font-size: 12px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-toolbar-chip:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  transform: translateY(-1px);
}

.hm-toolbar-chip.active {
  background: var(--hm-brand-light);
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-toolbar-chip.danger:hover {
  border-color: var(--hm-error);
  color: var(--hm-error);
}

.hm-chat-body {
  flex: 1;
  overflow: hidden;
}

.hm-msg-list {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 16px;
  height: 100%;
  overflow-y: auto;
  scroll-behavior: smooth;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.hm-msg-list::-webkit-scrollbar { display: none; }

.hm-chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 0;
}

.hm-empty-icon {
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

.hm-empty-icon:hover {
  transform: scale(1.08) rotate(-3deg);
}

.hm-empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
  letter-spacing: -0.2px;
}

.hm-empty-desc {
  font-size: 13px;
  color: var(--hm-font-tertiary);
  margin-bottom: 28px;
}

.hm-quick-cmds {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.hm-quick-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  font-size: 13px;
  color: var(--hm-font-primary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-quick-btn:hover {
  border-color: var(--hm-brand);
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-3px);
}

.hm-quick-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--hm-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hm-msg-time-divider {
  text-align: center;
  font-size: 11px;
  color: var(--hm-font-fourth);
  padding: 4px 0;
}

.hm-msg-item {
  display: flex;
  width: 100%;
  align-items: flex-start;
  gap: 10px;
  animation: hm-msg-in 0.35s var(--hm-spring);
}

.hm-msg-item.user {
  justify-content: flex-end;
}

.hm-msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--hm-radius-full);
  background: var(--hm-brand-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.hm-msg-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-msg-bubble {
  padding: 10px 14px;
  border-radius: var(--hm-radius-lg);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.assistant .hm-msg-bubble {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  color: var(--hm-font-primary);
  max-width: 85%;
}

.user .hm-msg-bubble {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  color: var(--hm-font-on-brand);
  max-width: 70%;
  box-shadow: var(--hm-shadow-brand);
}

.hm-msg-actions {
  display: flex;
  gap: 4px;
  padding-left: 4px;
  opacity: 0;
  transition: opacity 0.25s var(--hm-spring);
}

.hm-msg-item:hover .hm-msg-actions {
  opacity: 1;
}

.hm-msg-action {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  font-size: 11px;
  color: var(--hm-font-fourth);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
}

.hm-msg-action:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--hm-font-secondary);
  transform: translateY(-1px);
}

.hm-msg-action.active {
  background: rgba(10, 89, 247, 0.06);
}

.hm-msg-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.hm-msg-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
}

.hm-dots {
  display: flex;
  gap: 4px;
}

.hm-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--hm-brand);
  animation: hm-bounce 1.2s infinite ease-in-out;
}

.hm-dots span:nth-child(2) { animation-delay: 0.15s; }
.hm-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes hm-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.hm-loading-text {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}

.hm-loading-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--hm-brand);
  animation: hm-pulse 1.5s infinite ease-in-out;
}

@keyframes hm-pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.4; }
  50% { transform: scale(1.2); opacity: 1; }
}

@keyframes hm-msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.hm-chat-input-area {
  padding: 12px 16px 20px;
  flex-shrink: 0;
}

.hm-input-box {
  max-width: 720px;
  margin: 0 auto;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  padding: 10px 14px;
  transition: all 0.3s var(--hm-spring);
}

.hm-input-box:focus-within {
  border-color: var(--hm-brand);
  box-shadow: 0 0 0 3px rgba(10, 89, 247, 0.08);
}

.hm-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  background: transparent;
  font-family: inherit;
  color: var(--hm-font-primary);
}

.hm-textarea::placeholder {
  color: var(--hm-font-fourth);
}

.hm-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hm-input-chips {
  display: flex;
  gap: 6px;
}

.hm-mini-chip {
  padding: 3px 10px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  font-size: 12px;
  color: var(--hm-font-tertiary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-mini-chip:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  background: var(--hm-brand-light);
  transform: translateY(-1px);
}

.hm-send-btn {
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
}

.hm-send-btn.active {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  cursor: pointer;
  box-shadow: var(--hm-shadow-brand);
}

.hm-send-btn.active:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35);
}

@media (max-width: 768px) {
  .hm-sidebar {
    position: absolute;
    z-index: 10;
    height: 100%;
    box-shadow: var(--hm-shadow-md);
  }
  .hm-sidebar.collapsed {
    width: 0;
    border: none;
  }
}
</style>
