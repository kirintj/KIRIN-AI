import { request } from '@/utils'

export default {
  getDashboardOverview: () => request.get('/chat/dashboard/overview'),
  getTrackerChart: () => request.get('/chat/dashboard/tracker-chart'),
  getWeeklyActivity: () => request.get('/chat/dashboard/weekly-activity'),
}
