import { request } from '@/utils'

export default {
  addDocuments: (data = {}) => request.post('/chat/documents', data),
  clearDocuments: (params = {}) => request.delete('/chat/documents', { params }),
  getDocumentStats: () => request.get('/chat/documents/stats'),
  searchDocuments: (data = {}) => request.post('/chat/documents/search', data),
  listDocuments: (params = {}) => request.get('/chat/documents/list', { params }),
  getDocumentDetail: (params = {}) => request.get('/chat/documents/detail', { params }),
  uploadDocuments: (formData) => request.post('/chat/upload', formData),
}
