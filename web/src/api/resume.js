import { request } from '@/utils'

export default {
  getResumeTemplates: () => request.get('/chat/resume-export/templates'),
  generateResume: (data = {}) => request.post('/chat/resume-export/generate', data),
  exportResumeDocx: (data = {}) =>
    request.post('/chat/resume-export/export/docx', data, { responseType: 'blob' }),
  exportResumeText: (data = {}) => request.post('/chat/resume-export/export/text', data),
  getResumeExports: () => request.get('/chat/resume-export/exports'),
  downloadResumeExport: (filename) =>
    request.get(`/chat/resume-export/download/${filename}`, { responseType: 'blob' }),
}
