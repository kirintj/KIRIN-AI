import { request } from '@/utils'

export default {
  getTrackerApplications: (params = {}) => request.get('/chat/tracker/applications', { params }),
  createTrackerApplication: (data = {}) => request.post('/chat/tracker/applications', data),
  getTrackerApplication: (appId) => request.get(`/chat/tracker/applications/${appId}`),
  updateTrackerApplication: (data = {}) => request.put('/chat/tracker/applications', data),
  moveTrackerApplication: (data = {}) => request.put('/chat/tracker/applications/move', data),
  deleteTrackerApplication: (params = {}) =>
    request.delete('/chat/tracker/applications', { params }),
  getTrackerStats: () => request.get('/chat/tracker/applications/stats'),
}
