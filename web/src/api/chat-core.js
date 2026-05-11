import { request, createAxios } from '@/utils'

const chatRequest = createAxios({
  baseURL: import.meta.env.VITE_BASE_API,
  timeout: 120000,
})

export default {
  getHistory: () => request.get('/chat/history'),
  sendMessage: (data = {}) => chatRequest.post('/chat/chat', data),
  clearHistory: () => request.delete('/chat/history'),
  getModels: () => request.get('/chat/models'),
  agentChat: (data = {}) => chatRequest.post('/chat/agent', data),
  getAgentMemory: () => request.get('/chat/memory'),
  clearAgentMemory: () => request.delete('/chat/memory'),
  getChatHistoryList: (params = {}) => request.get('/chat/history/list', { params }),
  createChatHistory: (data = {}) => request.post('/chat/history/create', data),
  updateChatHistory: (data = {}) => request.post('/chat/history/update', data),
  deleteChatHistory: (params = {}) => request.delete('/chat/history/delete', { params }),
  getFeedbackList: () => request.get('/chat/feedback'),
  getLowRatingFeedback: (params = {}) => request.get('/chat/feedback/low-rating', { params }),
  getConversations: () => request.get('/chat/conversations'),
  createConversation: (data = {}) => request.post('/chat/conversations', data),
  renameConversation: (data = {}) => request.put('/chat/conversations/rename', data),
  deleteConversation: (params = {}) => request.delete('/chat/conversations/delete', { params }),
  getConversationMessages: (convId) => request.get(`/chat/conversations/${convId}/messages`),
  getRecentConversations: (params = {}) => request.get('/chat/conversations/recent', { params }),
}
