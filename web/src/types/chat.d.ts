export interface ChatMessage {
  role: string
  content: string
  timestamp?: string | null
}

export interface ChatRequest {
  messages: ChatMessage[]
  model?: string | null
  temperature?: number | null
  max_tokens?: number | null
}

export interface ChatResponse {
  message: ChatMessage
  model: string
  usage: Record<string, unknown> | null
}

export interface ChatHistoryItem {
  id: number
  username: string
  role: string
  content: string
  timestamp: string
}

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string | null
}

export interface Conversation {
  id: string
  title: string
  message_count?: number
  updated_at?: string
  created_at?: string
}

export interface ConversationGroup {
  label: string
  items: Conversation[]
}
