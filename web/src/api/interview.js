import { request } from '@/utils'

export default {
  getInterviewSessions: () => request.get('/chat/interview-sim/sessions'),
  createInterviewSession: (data = {}) => request.post('/chat/interview-sim/sessions', data),
  getInterviewSession: (sessionId) => request.get(`/chat/interview-sim/sessions/${sessionId}`),
  interviewChat: (data = {}) => request.post('/chat/interview-sim/sessions/chat', data),
  evaluateInterview: (data = {}) => request.post('/chat/interview-sim/sessions/evaluate', data),
  deleteInterviewSession: (params = {}) =>
    request.delete('/chat/interview-sim/sessions', { params }),
}
