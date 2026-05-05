import { ref } from 'vue'
import api from '@/api'

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
    window.$message?.error('仅支持文本、PDF、DOCX 类型文件')
    return false
  }
  if (file.size > maxSize) {
    window.$message?.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

export function validateAvatarFile(file) {
  if (!file.type?.startsWith('image/')) {
    window.$message?.error('仅支持上传图片文件')
    return false
  }
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowed.includes(file.type)) {
    window.$message?.error('仅支持 JPG/PNG/GIF/WebP 格式')
    return false
  }
  if (file.size > AVATAR_MAX_SIZE) {
    window.$message?.error('图片大小不能超过 5MB')
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
      window.$message?.success(res.data?.message || '文件上传成功')
      return res.data
    } catch (error) {
      console.error('文件上传失败', error)
      window.$message?.error('文件上传失败')
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
        window.$message?.success(`文件已解析（${res?.data?.pages || 1} 页）`)
        return res.data
      } else {
        window.$message?.warning('无法提取文件内容，请尝试粘贴文本')
        return null
      }
    } catch (err) {
      const msg = err?.response?.data?.msg || err?.message || '文件解析失败'
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
      window.$message?.success('头像上传成功')
      return res.data
    } catch (err) {
      window.$message?.error('头像上传失败')
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
