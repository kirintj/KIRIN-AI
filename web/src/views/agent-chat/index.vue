<script setup lang="ts">
import { useAgentChatStore } from '@/store/modules/agent-chat'
import { onMounted, watch, ref } from 'vue'
import { useMarkdown } from '@/composables/useMarkdown'
import TheIcon from '@/components/icon/TheIcon.vue'
import { NDrawer, NDrawerContent } from 'naive-ui'
import { useBreakpoints } from '@vueuse/core'
import ChatSidebar from './ChatSidebar.vue'
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

const agentStore = useAgentChatStore()
const message = ref('')
const { scrollToBottom } = useMarkdown()

const breakpoints = reactive(useBreakpoints({ sm: 768 }))
const isMobile = breakpoints.smaller('sm')

const sidebarCollapsed = ref(false)
const mobileDrawerVisible = ref(false)

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

const handleSwitchConversation = (convId: string) => {
  agentStore.switchConversation(convId)
  mobileDrawerVisible.value = false
}

const handleClearMemory = async () => {
  await agentStore.clearMemory()
  if (agentStore.currentConversationId) {
    await agentStore.deleteConversation(agentStore.currentConversationId)
  }
}

const safeScrollToBottom = () => {
  setTimeout(() => scrollToBottom('.hm-msg-list'), 30)
}

onMounted(async () => {
  await agentStore.loadConversations()
  if (agentStore.conversations.length > 0) {
    await agentStore.switchConversation(agentStore.conversations[0].id)
  }
  safeScrollToBottom()
})

watch(() => agentStore.messages, () => {
  scrollToBottom('.hm-msg-list')
}, { deep: true })
</script>

<template>
  <div class="hm-sidebar-layout">
    <template v-if="isMobile">
      <n-drawer v-model:show="mobileDrawerVisible" :width="280" placement="left" :auto-focus="false">
        <n-drawer-content :native-scrollbar="false" body-content-style="padding: 0;" title="对话">
          <ChatSidebar
            :conversations="agentStore.conversations"
            :filtered-conversations="agentStore.filteredConversations"
            :grouped-conversations="agentStore.groupedConversations"
            :current-conversation-id="agentStore.currentConversationId"
            :search-keyword="agentStore.searchKeyword"
            @update:search-keyword="agentStore.searchKeyword = $event"
            @switch="handleSwitchConversation"
            @new="agentStore.createConversation"
            @delete="agentStore.deleteConversation"
            @rename="agentStore.renameConversation"
          />
        </n-drawer-content>
      </n-drawer>
    </template>
    <template v-else>
      <div :class="['hm-sidebar', { collapsed: sidebarCollapsed }]">
        <div :class="['hm-sidebar-header', { collapsed: sidebarCollapsed }]">
          <span v-if="!sidebarCollapsed" class="hm-sidebar-title">对话</span>
          <button v-if="!sidebarCollapsed" class="hm-sidebar-new-btn" @click="agentStore.createConversation">
            <TheIcon icon="icon-park-outline:plus" :size="16" />
          </button>
          <button class="hm-sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
            <TheIcon :icon="sidebarCollapsed ? 'icon-park-outline:right' : 'icon-park-outline:left'" :size="14" />
          </button>
        </div>
        <div v-if="!sidebarCollapsed" class="hm-sidebar-body">
          <ChatSidebar
            :conversations="agentStore.conversations"
            :filtered-conversations="agentStore.filteredConversations"
            :grouped-conversations="agentStore.groupedConversations"
            :current-conversation-id="agentStore.currentConversationId"
            :search-keyword="agentStore.searchKeyword"
            @update:search-keyword="agentStore.searchKeyword = $event"
            @switch="handleSwitchConversation"
            @new="agentStore.createConversation"
            @delete="agentStore.deleteConversation"
            @rename="agentStore.renameConversation"
          />
        </div>
      </div>
    </template>

    <div class="hm-chat-page">
      <div class="hm-toolbar">
        <div class="hm-toolbar-left">
          <button v-if="isMobile" class="hm-mobile-conv-btn" @click="mobileDrawerVisible = true">
            <TheIcon icon="icon-park-outline:chat" :size="16" />
          </button>
          <span class="hm-chat-title">AI Agent</span>
          <span v-if="!isMobile" class="hm-chat-badge">智能对话</span>
        </div>
        <div class="hm-toolbar-right">
          <button
            v-if="!isMobile"
            class="hm-toolbar-chip"
            :class="{ active: agentStore.useLangGraph }"
            @click="agentStore.useLangGraph = !agentStore.useLangGraph"
          >
            <TheIcon icon="icon-park-outline:mindmap-map" :size="14" />
            {{ agentStore.useLangGraph ? 'LangGraph' : '经典' }}
          </button>
          <button
            v-if="!isMobile"
            class="hm-toolbar-chip"
            :class="{ active: agentStore.useLlmRouter }"
            @click="agentStore.useLlmRouter = !agentStore.useLlmRouter"
          >
            <TheIcon icon="icon-park-outline:brain" :size="14" />
            LLM 路由
          </button>
          <button class="hm-toolbar-chip danger" @click="handleClearMemory">
            <TheIcon icon="icon-park-outline:delete" :size="14" />
            <span v-if="!isMobile">清空</span>
          </button>
        </div>
      </div>

      <div class="hm-chat-body">
        <ChatMessages
          :messages="agentStore.messages"
          :is-loading="agentStore.isLoading"
          @regenerate="agentStore.regenerateMessage"
          @quick-send="quickSend"
        />
      </div>

      <ChatInput
        v-model="message"
        :is-loading="agentStore.isLoading"
        @send="sendMessage"
        @quick-send="quickSend"
      />
    </div>
  </div>
</template>

<style scoped>
.hm-sidebar-layout {
  height: 100%;
}

.hm-sidebar {
  width: 260px;
  border-right: 1px solid var(--hm-border);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
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
  justify-content: space-between;
  padding: 12px;
  flex-shrink: 0;
}

.hm-sidebar-header.collapsed {
  justify-content: center;
  padding: 12px 8px;
}

.hm-sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-sidebar-new-btn {
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
  transition: all 0.25s var(--hm-spring);
}

.hm-sidebar-new-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  background: var(--hm-brand-light);
  transform: scale(1.05);
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
}

.hm-sidebar-body {
  flex: 1;
  overflow: hidden;
}

.hm-chat-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--hm-bg-primary);
  overflow: hidden;
  min-width: 0;
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

.hm-chat-body {
  flex: 1;
  overflow: hidden;
}

.hm-mobile-conv-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-sm);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-secondary);
  transition: all 0.25s var(--hm-spring);
}

.hm-mobile-conv-btn:active {
  background: var(--hm-brand-light);
  color: var(--hm-brand);
  transform: scale(0.92);
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
