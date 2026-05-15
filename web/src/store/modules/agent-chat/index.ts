import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import i18n from '~/i18n'
import type { AgentMessage, Conversation, ConversationGroup } from '@/types/chat'

const t = i18n.global.t

export const useAgentChatStore = defineStore('agent-chat', () => {
  const messages = ref<AgentMessage[]>([])
  const isLoading = ref(false)
  const useLlmRouter = ref(false)
  const useLangGraph = ref(true)

  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string | null>(null)
  const searchKeyword = ref('')

  const filteredConversations = computed(() => {
    const keyword = searchKeyword.value.trim().toLowerCase()
    if (!keyword) return conversations.value
    return conversations.value.filter((c) => (c.title || '').toLowerCase().includes(keyword))
  })

  const groupedConversations = computed<ConversationGroup[]>(() => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 86400000)
    const weekAgo = new Date(today.getTime() - 6 * 86400000)

    const groups: ConversationGroup[] = [
      { label: t('common.messages.today'), items: [] },
      { label: t('common.messages.yesterday'), items: [] },
      { label: t('common.messages.recent_7_days'), items: [] },
      { label: t('common.messages.earlier'), items: [] },
    ]

    for (const conv of filteredConversations.value) {
      const date = conv.updated_at ? new Date(conv.updated_at) : new Date(conv.created_at || 0)
      if (date >= today) {
        groups[0].items.push(conv)
      } else if (date >= yesterday) {
        groups[1].items.push(conv)
      } else if (date >= weekAgo) {
        groups[2].items.push(conv)
      } else {
        groups[3].items.push(conv)
      }
    }

    return groups.filter((g) => g.items.length > 0)
  })

  function newMessage(role: 'user' | 'assistant', content: string, timestamp?: string | null): AgentMessage {
    return {
      id: crypto.randomUUID(),
      role,
      content,
      timestamp: timestamp ?? new Date().toISOString(),
    }
  }

  const loadConversations = async () => {
    try {
      const res = await api.getConversations()
      conversations.value = (res.data || []).map((c: any) => ({ ...c, id: String(c.id) }))
    } catch (error) {
      console.error('加载会话列表失败', error)
    }
  }

  const createConversation = async (title?: string) => {
    try {
      const res = await api.createConversation({ title: title || t('common.messages.new_conversation') })
      const conv: Conversation = res.data
      conversations.value.unshift(conv)
      currentConversationId.value = String(conv.id)
      messages.value = []
      return conv
    } catch (error) {
      console.error('创建会话失败', error)
      return null
    }
  }

  const switchConversation = async (convId: string) => {
    if (String(convId) === currentConversationId.value) return
    currentConversationId.value = String(convId)
    try {
      const res = await api.getConversationMessages(convId)
      messages.value = (res.data || []).map((m: any) =>
        newMessage(m.role, m.content, m.timestamp || m.created_at || null),
      )
    } catch (error) {
      console.error('加载会话消息失败', error)
      messages.value = []
    }
  }

  const renameConversation = async (convId: string, title: string) => {
    try {
      await api.renameConversation({ conversation_id: convId, title })
      const conv = conversations.value.find((c) => c.id === convId)
      if (conv) conv.title = title
    } catch (error) {
      console.error('重命名失败', error)
    }
  }

  const deleteConversation = async (convId: string) => {
    try {
      await api.deleteConversation({ conversation_id: convId })
      conversations.value = conversations.value.filter((c) => c.id !== convId)
      if (currentConversationId.value === convId) {
        currentConversationId.value = null
        messages.value = []
        if (conversations.value.length > 0) {
          await switchConversation(conversations.value[0].id)
        }
      }
    } catch (error) {
      console.error('删除会话失败', error)
    }
  }

  const loadMemory = async () => {
    try {
      const res = await api.getAgentMemory()
      const history = res.data || []
      messages.value = history.flatMap((item: any) => [
        newMessage('user', item.user, item.created_at || null),
        newMessage('assistant', item.assistant, item.created_at || null),
      ])
    } catch (error) {
      console.error('加载记忆失败', error)
    }
  }

  const _buildRequestParams = (query: string) => ({
    query,
    use_llm_router: useLlmRouter.value,
    use_langgraph: useLangGraph.value,
    conversation_id: currentConversationId.value,
  })

  const sendMessage = async (query: string) => {
    if (!query || !query.trim() || isLoading.value) return

    messages.value.push(newMessage('user', query))
    isLoading.value = true

    try {
      const res = await api.agentChat(_buildRequestParams(query))
      messages.value.push(newMessage('assistant', res.data?.answer || t('common.messages.no_response')))
      if (currentConversationId.value) {
        await loadConversations()
      }
    } catch (error) {
      console.error('Agent 请求失败：', error)
      messages.value.push(newMessage('assistant', t('common.messages.request_failed')))
    } finally {
      isLoading.value = false
    }
  }

  const regenerateMessage = async (messageIndex: number) => {
    if (isLoading.value) return

    // Find the nearest user message before this index
    let userMsg: AgentMessage | undefined
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') {
        userMsg = messages.value[i]
        break
      }
    }
    if (!userMsg) return

    messages.value.splice(messageIndex, 1)
    isLoading.value = true

    try {
      const res = await api.agentChat(_buildRequestParams(userMsg.content))
      messages.value.push(newMessage('assistant', res.data?.answer || t('common.messages.no_response')))
    } catch (error) {
      console.error('重新生成失败：', error)
      messages.value.push(newMessage('assistant', t('common.messages.regenerate_failed')))
    } finally {
      isLoading.value = false
    }
  }

  const clearMemory = async () => {
    try {
      await api.clearAgentMemory()
      messages.value = []
    } catch (error) {
      console.error('清空记忆失败', error)
    }
  }

  return {
    messages,
    isLoading,
    useLlmRouter,
    useLangGraph,
    conversations,
    currentConversationId,
    searchKeyword,
    filteredConversations,
    groupedConversations,
    loadConversations,
    createConversation,
    switchConversation,
    renameConversation,
    deleteConversation,
    loadMemory,
    sendMessage,
    regenerateMessage,
    clearMemory,
  }
})
