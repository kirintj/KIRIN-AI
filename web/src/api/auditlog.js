import { request } from '@/utils'

export default {
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
}
