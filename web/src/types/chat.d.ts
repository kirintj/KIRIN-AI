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
