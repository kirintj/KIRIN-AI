import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAgentChatStore = defineStore('agent-chat', () => {
  const messages = ref([])
  const isLoading = ref(false)
  const useLlmRouter = ref(false)
  const useLangGraph = ref(true)

  const conversations = ref([])
  const currentConversationId = ref(null)
  const searchKeyword = ref('')

  const filteredConversations = computed(() => {
    const keyword = searchKeyword.value.trim().toLowerCase()
    if (!keyword) return conversations.value
    return conversations.value.filter((c) => (c.title || '').toLowerCase().includes(keyword))
  })

  const groupedConversations = computed(() => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 86400000)
    const weekAgo = new Date(today.getTime() - 6 * 86400000)

    const groups = [
      { label: '今天', items: [] },
      { label: '昨天', items: [] },
      { label: '最近7天', items: [] },
      { label: '更早', items: [] },
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

  const loadConversations = async () => {
    try {
      const res = await api.getConversations()
      conversations.value = res.data || []
    } catch (error) {
      console.error('加载会话列表失败', error)
    }
  }

  const createConversation = async (title = '新对话') => {
    try {
      const res = await api.createConversation({ title })
      const conv = res.data
      conversations.value.unshift(conv)
      currentConversationId.value = conv.id
      messages.value = []
      return conv
    } catch (error) {
      console.error('创建会话失败', error)
      return null
    }
  }

  const switchConversation = async (convId) => {
    if (convId === currentConversationId.value) return
    currentConversationId.value = convId
    try {
      const res = await api.getConversationMessages(convId)
      messages.value = (res.data || []).map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp || m.created_at || null,
      }))
    } catch (error) {
      console.error('加载会话消息失败', error)
      messages.value = []
    }
  }

  const renameConversation = async (convId, title) => {
    try {
      await api.renameConversation({ conversation_id: convId, title })
      const conv = conversations.value.find((c) => c.id === convId)
      if (conv) conv.title = title
    } catch (error) {
      console.error('重命名失败', error)
    }
  }

  const deleteConversation = async (convId) => {
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
      messages.value = history.flatMap((item) => [
        { role: 'user', content: item.user, timestamp: item.created_at || null },
        { role: 'assistant', content: item.assistant, timestamp: item.created_at || null },
      ])
    } catch (error) {
      console.error('加载记忆失败', error)
    }
  }

  const _buildRequestParams = (query) => ({
    query,
    use_llm_router: useLlmRouter.value,
    use_langgraph: useLangGraph.value,
    conversation_id: currentConversationId.value,
  })

  const sendMessage = async (query) => {
    if (!query || !query.trim() || isLoading.value) return

    const now = new Date().toISOString()
    messages.value.push({ role: 'user', content: query, timestamp: now })
    isLoading.value = true

    try {
      const res = await api.agentChat(_buildRequestParams(query))
      messages.value.push({
        role: 'assistant',
        content: res.data?.answer || '无返回',
        timestamp: new Date().toISOString(),
      })
      if (currentConversationId.value) {
        await loadConversations()
      }
    } catch (error) {
      console.error('Agent 请求失败：', error)
      messages.value.push({
        role: 'assistant',
        content: '请求失败，请检查后端服务',
        timestamp: new Date().toISOString(),
      })
    } finally {
      isLoading.value = false
    }
  }

  const regenerateMessage = async (messageIndex) => {
    if (isLoading.value) return

    const userMsg = messages.value[messageIndex - 1]
    if (!userMsg || userMsg.role !== 'user') return

    messages.value.splice(messageIndex, 1)
    isLoading.value = true

    try {
      const res = await api.agentChat(_buildRequestParams(userMsg.content))
      messages.value.push({
        role: 'assistant',
        content: res.data?.answer || '无返回',
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      console.error('重新生成失败：', error)
      messages.value.push({
        role: 'assistant',
        content: '重新生成失败，请重试',
        timestamp: new Date().toISOString(),
      })
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
