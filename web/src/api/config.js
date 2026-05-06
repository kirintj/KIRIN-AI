import { request } from '@/utils'

export default {
  getAiConfig: () => request.get('/config/ai'),
  updateAiConfig: (data = {}) => request.post('/config/ai', data),
}
