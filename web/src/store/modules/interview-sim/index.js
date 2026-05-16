import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import i18n from '~/i18n'

const t = i18n.global.t

export const useInterviewStore = defineStore('interview-sim', () => {
  const sessions = ref([])
  const currentSession = ref(null)
  const messages = ref([])
  const isLoading = ref(false)
  const isEvaluating = ref(false)

  const INTERVIEW_TYPES = computed(() => {
    void i18n.global.locale.value
    return {
      tech: t('common.interview.type_tech'),
      hr: t('common.interview.type_hr'),
      behavior: t('common.interview.type_behavior'),
      case: t('common.interview.type_case'),
    }
  })

  const loadSessions = async () => {
    try {
      const res = await api.getInterviewSessions()
      sessions.value = res.data || []
    } catch (error) {
      console.error('加载面试会话失败', error)
    }
  }

  const createSession = async (data) => {
    try {
      const res = await api.createInterviewSession(data)
      const session = res.data
      currentSession.value = session
      messages.value = session.messages || []
      sessions.value.unshift({
        id: session.id,
        company: session.company,
        position: session.position,
        interview_type: session.interview_type,
        status: session.status,
        score: session.score,
        created_at: session.created_at,
        updated_at: session.updated_at,
      })
      return session
    } catch (error) {
      console.error('创建面试会话失败', error)
      return null
    }
  }

  const loadSession = async (sessionId) => {
    try {
      const res = await api.getInterviewSession(sessionId)
      currentSession.value = res.data
      messages.value = res.data?.messages || []
    } catch (error) {
      console.error('加载面试会话详情失败', error)
    }
  }

  const sendMessage = async (text) => {
    if (!currentSession.value || !text.trim() || isLoading.value) return

    messages.value.push({ role: 'user', content: text })
    isLoading.value = true

    try {
      const res = await api.interviewChat({
        session_id: currentSession.value.id,
        message: text,
      })
      messages.value.push({ role: 'assistant', content: res.data?.reply || t('common.messages.no_reply') })
    } catch (error) {
      console.error('面试对话失败', error)
      messages.value.push({ role: 'assistant', content: t('common.messages.interview_request_failed') })
    } finally {
      isLoading.value = false
    }
  }

  const evaluateCurrentSession = async () => {
    if (!currentSession.value || isEvaluating.value) return
    isEvaluating.value = true

    try {
      const res = await api.evaluateInterview({ session_id: currentSession.value.id })
      if (currentSession.value) {
        currentSession.value.status = 'completed'
        currentSession.value.score = res.data?.score
        currentSession.value.evaluation = res.data
      }
      const session = sessions.value.find((s) => s.id === currentSession.value?.id)
      if (session) {
        session.status = 'completed'
        session.score = res.data?.score
      }
      return res.data
    } catch (error) {
      console.error('面试评估失败', error)
      return null
    } finally {
      isEvaluating.value = false
    }
  }

  const deleteSession = async (sessionId) => {
    try {
      await api.deleteInterviewSession({ session_id: sessionId })
      sessions.value = sessions.value.filter((s) => s.id !== sessionId)
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
        messages.value = []
      }
    } catch (error) {
      console.error('删除面试会话失败', error)
    }
  }

  const resetCurrentSession = () => {
    currentSession.value = null
    messages.value = []
  }

  return {
    sessions,
    currentSession,
    messages,
    isLoading,
    isEvaluating,
    INTERVIEW_TYPES,
    loadSessions,
    createSession,
    loadSession,
    sendMessage,
    evaluateCurrentSession,
    deleteSession,
    resetCurrentSession,
  }
})
