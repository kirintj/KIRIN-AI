import { ref } from 'vue'
import api from '@/api'
import i18n from '~/i18n'

const t = i18n.global.t

const DOCUMENT_EXTENSIONS = [
  '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
  '.yaml', '.yml', '.sh', '.sql', '.java', '.go', '.rs', '.c', '.cpp',
  '.log', '.ini', '.cfg', '.toml', '.csv', '.pdf', '.docx',
]

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024
const AVATAR_MAX_SIZE = 5 * 1024 * 1024

function getFileExtension(filename) {
  if (!filename) return ''
  const idx = filename.lastIndexOf('.')
  return idx >= 0 ? filename.substring(idx).toLowerCase() : ''
}

export function validateDocumentFile(file, maxSize = DEFAULT_MAX_SIZE) {
  const ext = getFileExtension(file.name)
  if (!DOCUMENT_EXTENSIONS.includes(ext)) {
    window.$message?.error(t('common.upload.file_type_error'))
    return false
  }
  if (file.size > maxSize) {
    window.$message?.error(t('common.upload.file_size_error'))
    return false
  }
  return true
}

export function validateAvatarFile(file) {
  if (!file.type?.startsWith('image/')) {
    window.$message?.error(t('common.upload.image_type_error'))
    return false
  }
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowed.includes(file.type)) {
    window.$message?.error(t('common.upload.image_format_error'))
    return false
  }
  if (file.size > AVATAR_MAX_SIZE) {
    window.$message?.error(t('common.upload.image_size_error'))
    return false
  }
  return true
}

export function useFileUpload() {
  const uploading = ref(false)

  const uploadToKnowledgeBase = async (rawFile, collection, docType = '') => {
    if (!validateDocumentFile(rawFile)) return null

    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('files', rawFile)
      formData.append('collection', collection)
      formData.append('doc_type', docType)
      const res = await api.uploadDocuments(formData)
      window.$message?.success(res.data?.message || t('common.upload.upload_success'))
      return res.data
    } catch (error) {
      console.error('文件上传失败', error)
      window.$message?.error(t('common.upload.upload_failed'))
      return null
    } finally {
      uploading.value = false
    }
  }

  const parseFile = async (rawFile) => {
    if (!validateDocumentFile(rawFile)) return null

    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('file', rawFile)
      const res = await api.parseFile(formData)
      const text = res?.data?.text
      if (text && text.trim()) {
        window.$message?.success(t('common.upload.parse_success', { pages: res?.data?.pages || 1 }))
        return res.data
      } else {
        window.$message?.warning(t('common.upload.parse_empty'))
        return null
      }
    } catch (err) {
      const msg = err?.response?.data?.msg || err?.message || t('common.upload.parse_failed')
      window.$message?.error(msg)
      return null
    } finally {
      uploading.value = false
    }
  }

  const uploadAvatar = async (rawFile) => {
    if (!validateAvatarFile(rawFile)) return null

    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('file', rawFile)
      const res = await api.uploadAvatar(formData)
      window.$message?.success(t('common.upload.avatar_upload_success'))
      return res.data
    } catch (err) {
      window.$message?.error(t('common.upload.avatar_upload_failed'))
      return null
    } finally {
      uploading.value = false
    }
  }

  return {
    uploading,
    uploadToKnowledgeBase,
    parseFile,
    uploadAvatar,
  }
}
