import { createAxios } from '@/utils'

const jobRequest = createAxios({
  baseURL: import.meta.env.VITE_BASE_API,
  timeout: 120000,
})

export default {
  jobParseResume: (data = {}) => jobRequest.post('/chat/job/resume', data),
  jobParseJD: (data = {}) => jobRequest.post('/chat/job/jd', data),
  jobMatch: (data = {}) => jobRequest.post('/chat/job/match', data),
  jobOptimize: (data = {}) => jobRequest.post('/chat/job/optimize', data),
  jobOptimizeRag: (data = {}) => jobRequest.post('/chat/job/optimize-rag', data),
  jobPlan: (data = {}) => jobRequest.post('/chat/job/plan', data),
  jobPipeline: (data = {}) => jobRequest.post('/chat/job/pipeline', data),
  jobInterview: (data = {}) => jobRequest.post('/chat/job/interview', data),
  jobSalary: (data = {}) => jobRequest.post('/chat/job/salary', data),
  jobGuide: (data = {}) => jobRequest.post('/chat/job/guide', data),
  jobFeedback: (data = {}) => jobRequest.post('/chat/job/feedback', data),
  parseFile: (formData) => jobRequest.post('/chat/job/parse-file', formData),
}
