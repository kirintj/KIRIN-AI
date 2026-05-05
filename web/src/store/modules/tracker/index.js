import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useTrackerStore = defineStore('tracker', () => {
  const applications = ref([])
  const stats = ref(null)
  const isLoading = ref(false)
  const viewMode = ref('kanban')
  const searchKeyword = ref('')

  const STATUS_LIST = ['wishlist', 'applied', 'screening', 'interview', 'offer', 'rejected']
  const STATUS_LABELS = {
    wishlist: '意向',
    applied: '已投递',
    screening: '筛选中',
    interview: '面试中',
    offer: '已录用',
    rejected: '已拒绝',
  }
  const STATUS_COLORS = {
    wishlist: '#86909C',
    applied: '#0A59F7',
    screening: '#722ED1',
    interview: '#ED6F21',
    offer: '#64BB5C',
    rejected: '#E84026',
  }

  const loadApplications = async (status = null) => {
    isLoading.value = true
    try {
      const params = {}
      if (status) params.status = status
      const res = await api.getTrackerApplications(params)
      applications.value = res.data || []
    } catch (error) {
      console.error('加载求职记录失败', error)
    } finally {
      isLoading.value = false
    }
  }

  const loadStats = async () => {
    try {
      const res = await api.getTrackerStats()
      stats.value = res.data || null
    } catch (error) {
      console.error('加载统计数据失败', error)
    }
  }

  const createApplication = async (data) => {
    try {
      const res = await api.createTrackerApplication(data)
      const app = res.data
      applications.value.unshift(app)
      await loadStats()
      return app
    } catch (error) {
      console.error('创建求职记录失败', error)
      return null
    }
  }

  const updateApplication = async (appId, updates) => {
    try {
      await api.updateTrackerApplication({ app_id: appId, ...updates })
      const app = applications.value.find((a) => a.id === appId)
      if (app) Object.assign(app, updates, { updated_at: new Date().toISOString() })
      await loadStats()
      return true
    } catch (error) {
      console.error('更新求职记录失败', error)
      return false
    }
  }

  const moveApplication = async (appId, newStatus) => {
    try {
      await api.moveTrackerApplication({ app_id: appId, status: newStatus })
      const app = applications.value.find((a) => a.id === appId)
      if (app) {
        app.status = newStatus
        app.updated_at = new Date().toISOString()
      }
      await loadStats()
      return true
    } catch (error) {
      console.error('移动求职记录失败', error)
      return false
    }
  }

  const deleteApplication = async (appId) => {
    try {
      await api.deleteTrackerApplication({ app_id: appId })
      applications.value = applications.value.filter((a) => a.id !== appId)
      await loadStats()
      return true
    } catch (error) {
      console.error('删除求职记录失败', error)
      return false
    }
  }

  const getApplicationsByStatus = (status) => {
    return applications.value.filter((a) => a.status === status)
  }

  const filteredApplications = computed(() => {
    const keyword = searchKeyword.value.trim().toLowerCase()
    if (!keyword) return applications.value
    return applications.value.filter((a) =>
      (a.company || '').toLowerCase().includes(keyword) ||
      (a.position || '').toLowerCase().includes(keyword)
    )
  })

  const timelineApplications = computed(() => {
    return [...applications.value]
      .filter((a) => a.created_at)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  })

  return {
    applications,
    stats,
    isLoading,
    viewMode,
    searchKeyword,
    STATUS_LIST,
    STATUS_LABELS,
    STATUS_COLORS,
    loadApplications,
    loadStats,
    createApplication,
    updateApplication,
    moveApplication,
    deleteApplication,
    getApplicationsByStatus,
    filteredApplications,
    timelineApplications,
  }
})
