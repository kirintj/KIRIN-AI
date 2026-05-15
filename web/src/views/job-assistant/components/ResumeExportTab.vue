<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { formatShortDate } from '@/utils/common/time'

const { t } = useI18n()

const emit = defineEmits(['feedback'])

const templates = ref<Record<string, string>>({})
const selectedTemplate = ref('classic')
const resumeInput = ref('')
const resumeData = ref<any>(null)
const isGenerating = ref(false)
const isExporting = ref(false)
const exportList = ref<any[]>([])

const loadTemplates = async () => {
  try {
    const res = await api.getResumeTemplates()
    templates.value = res.data || {}
  } catch (error) {
    console.error('Failed to load templates', error)
  }
}

const loadExports = async () => {
  try {
    const res = await api.getResumeExports()
    exportList.value = res.data || []
  } catch (error) {
    console.error('Failed to load exports', error)
  }
}

const generateResume = async () => {
  if (!resumeInput.value.trim()) {
    window.$message?.warning(t('views.job_assistant.msg_enter_info'))
    return
  }
  isGenerating.value = true
  try {
    const res = await api.generateResume({
      user_info: resumeInput.value,
      template: selectedTemplate.value,
    })
    resumeData.value = res.data
    window.$message?.success(t('views.job_assistant.msg_resume_generated'))
  } catch (error) {
    window.$message?.error(t('views.job_assistant.msg_resume_failed'))
  } finally {
    isGenerating.value = false
  }
}

const exportDocx = async () => {
  if (!resumeData.value) {
    window.$message?.warning(t('views.job_assistant.msg_generate_first'))
    return
  }
  isExporting.value = true
  try {
    const res = await api.exportResumeDocx({
      resume_data: resumeData.value,
      template: selectedTemplate.value,
    })
    const blob = new Blob([res], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${resumeData.value.name || 'resume'}.docx`
    link.click()
    window.URL.revokeObjectURL(url)
    window.$message?.success(t('views.job_assistant.msg_docx_success'))
    loadExports()
  } catch (error) {
    window.$message?.error(t('views.job_assistant.msg_docx_failed'))
  } finally {
    isExporting.value = false
  }
}

const exportText = async () => {
  if (!resumeData.value) {
    window.$message?.warning(t('views.job_assistant.msg_generate_first'))
    return
  }
  try {
    const res = await api.exportResumeText({ resume_data: resumeData.value })
    const text = res.data?.text || ''
    const blob = new Blob([text], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${resumeData.value.name || 'resume'}.md`
    link.click()
    window.URL.revokeObjectURL(url)
    window.$message?.success(t('views.job_assistant.msg_markdown_success'))
  } catch (error) {
    window.$message?.error(t('views.job_assistant.msg_text_failed'))
  }
}

const downloadFile = async (filename: string) => {
  try {
    const res = await api.downloadResumeExport(filename)
    const blob = new Blob([res], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    window.$message?.error(t('views.job_assistant.msg_download_failed'))
  }
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  return (bytes / 1024).toFixed(1) + ' KB'
}

onMounted(() => {
  loadTemplates()
  loadExports()
})
</script>

<template>
  <div class="hm-export-tab">
    <div class="hm-ex-section">
      <div class="hm-ex-section-header">
        <div class="hm-ex-section-icon" style="background: rgba(10,89,247,0.08)">
          <TheIcon icon="icon-park-outline:edit-name" :size="18" color="#0A59F7" />
        </div>
        <span class="hm-ex-section-title">{{ t('views.job_assistant.export_input_info') }}</span>
      </div>
      <textarea
        v-model="resumeInput"
        class="hm-ex-textarea"
        :placeholder="t('views.job_assistant.export_info_placeholder')"
        :disabled="isGenerating"
      ></textarea>
    </div>

    <div class="hm-ex-section">
      <div class="hm-ex-section-header">
        <div class="hm-ex-section-icon" style="background: rgba(114,46,209,0.08)">
          <TheIcon icon="icon-park-outline:template" :size="18" color="#722ED1" />
        </div>
        <span class="hm-ex-section-title">{{ t('views.job_assistant.export_select_template') }}</span>
      </div>
      <div class="hm-ex-templates">
        <button
          v-for="(label, key) in templates"
          :key="key"
          :class="['hm-ex-template-chip', { active: selectedTemplate === key }]"
          @click="selectedTemplate = key"
        >
          {{ label }}
        </button>
      </div>
    </div>

    <div class="hm-ex-actions">
      <button
        class="hm-ex-btn primary"
        :disabled="!resumeInput.trim() || isGenerating"
        @click="generateResume"
      >
        <TheIcon v-if="isGenerating" icon="icon-park-outline:loading" :size="16" color="#fff" />
        <TheIcon v-else icon="icon-park-outline:magic" :size="16" color="#fff" />
        {{ isGenerating ? t('views.job_assistant.btn_generating') : t('views.job_assistant.btn_generate_resume') }}
      </button>
    </div>

    <div v-if="resumeData" class="hm-ex-section">
      <div class="hm-ex-section-header">
        <div class="hm-ex-section-icon" style="background: rgba(100,187,92,0.08)">
          <TheIcon icon="icon-park-outline:preview-open" :size="18" color="#64BB5C" />
        </div>
        <span class="hm-ex-section-title">{{ t('views.job_assistant.export_preview') }}</span>
      </div>
      <div class="hm-ex-preview">
        <div class="hm-ex-preview-header">
          <h3 class="hm-ex-preview-name">{{ resumeData.name || t('views.job_assistant.unnamed') }}</h3>
          <span v-if="resumeData.title" class="hm-ex-preview-title">{{ resumeData.title }}</span>
        </div>
        <div v-if="resumeData.phone || resumeData.email" class="hm-ex-preview-contact">
          <span v-if="resumeData.phone">{{ resumeData.phone }}</span>
          <span v-if="resumeData.phone && resumeData.email"> | </span>
          <span v-if="resumeData.email">{{ resumeData.email }}</span>
        </div>
        <div v-if="resumeData.summary" class="hm-ex-preview-block">
          <div class="hm-ex-preview-label">{{ t('views.job_assistant.section_summary') }}</div>
          <p class="hm-ex-preview-text">{{ resumeData.summary }}</p>
        </div>
        <div v-if="resumeData.skills?.length" class="hm-ex-preview-block">
          <div class="hm-ex-preview-label">{{ t('views.job_assistant.section_skills') }}</div>
          <div class="hm-ex-preview-tags">
            <span v-for="skill in resumeData.skills" :key="skill" class="hm-ex-tag">{{ skill }}</span>
          </div>
        </div>
        <div v-if="resumeData.experience?.length" class="hm-ex-preview-block">
          <div class="hm-ex-preview-label">{{ t('views.job_assistant.section_experience') }}</div>
          <div v-for="(exp, i) in resumeData.experience" :key="i" class="hm-ex-preview-item">
            <div class="hm-ex-preview-item-header">
              <span class="hm-ex-preview-item-title">{{ exp.company }} - {{ exp.position }}</span>
              <span v-if="exp.period" class="hm-ex-preview-item-period">{{ exp.period }}</span>
            </div>
            <p v-if="exp.description" class="hm-ex-preview-text">{{ exp.description }}</p>
          </div>
        </div>
        <div v-if="resumeData.education?.length" class="hm-ex-preview-block">
          <div class="hm-ex-preview-label">{{ t('views.job_assistant.section_education') }}</div>
          <div v-for="(edu, i) in resumeData.education" :key="i" class="hm-ex-preview-item">
            <span>{{ edu.school }} | {{ edu.major }} | {{ edu.degree }} <span v-if="edu.period">({{ edu.period }})</span></span>
          </div>
        </div>
      </div>

      <div class="hm-ex-export-actions">
        <button class="hm-ex-btn" :disabled="isExporting" @click="exportDocx">
          <TheIcon icon="icon-park-outline:doc-detail" :size="16" />
          {{ isExporting ? t('views.job_assistant.btn_exporting') : t('views.job_assistant.btn_export_docx') }}
        </button>
        <button class="hm-ex-btn" @click="exportText">
          <TheIcon icon="icon-park-outline:file-text" :size="16" />
          {{ t('views.job_assistant.btn_export_markdown') }}
        </button>
      </div>
    </div>

    <div v-if="exportList.length > 0" class="hm-ex-section">
      <div class="hm-ex-section-header">
        <div class="hm-ex-section-icon" style="background: rgba(237,111,33,0.08)">
          <TheIcon icon="icon-park-outline:folder" :size="18" color="#ED6F21" />
        </div>
        <span class="hm-ex-section-title">{{ t('views.job_assistant.export_history') }}</span>
      </div>
      <div class="hm-ex-file-list">
        <div
          v-for="file in exportList"
          :key="file.filename"
          class="hm-ex-file-item"
          @click="downloadFile(file.filename)"
        >
          <TheIcon icon="icon-park-outline:file-word" :size="20" color="#0A59F7" />
          <div class="hm-ex-file-info">
            <span class="hm-ex-file-name">{{ file.filename }}</span>
            <span class="hm-ex-file-meta">{{ formatSize(file.size) }} · {{ formatShortDate(file.created_at) }}</span>
          </div>
          <TheIcon icon="icon-park-outline:download" :size="16" color="var(--hm-font-fourth)" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hm-export-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hm-ex-section {
  background: var(--hm-bg-secondary);
  border-radius: var(--hm-radius-lg);
  padding: 20px;
  box-shadow: var(--hm-shadow-sm);
}

.hm-ex-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.hm-ex-section-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--hm-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hm-ex-section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-ex-textarea {
  width: 100%;
  min-height: 160px;
  padding: 12px 14px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-md);
  background: var(--hm-bg-container);
  color: var(--hm-font-primary);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
}

.hm-ex-textarea:focus {
  border-color: var(--hm-brand);
}

.hm-ex-textarea::placeholder {
  color: var(--hm-font-fourth);
}

.hm-ex-templates {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hm-ex-template-chip {
  padding: 6px 16px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-container);
  font-size: 13px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.hm-ex-template-chip:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-ex-template-chip.active {
  background: var(--hm-brand);
  border-color: var(--hm-brand);
  color: var(--hm-font-on-brand);
}

.hm-ex-actions {
  display: flex;
  gap: 10px;
}

.hm-ex-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-md);
  background: var(--hm-bg-secondary);
  font-size: 14px;
  color: var(--hm-font-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.hm-ex-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
}

.hm-ex-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hm-ex-btn.primary {
  background: var(--hm-brand);
  border-color: var(--hm-brand);
  color: var(--hm-font-on-brand);
}

.hm-ex-btn.primary:hover {
  background: var(--hm-brand-hover);
}

.hm-ex-preview {
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-md);
  padding: 20px;
  background: var(--hm-bg-container);
}

.hm-ex-preview-header {
  margin-bottom: 8px;
}

.hm-ex-preview-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--hm-font-primary);
  margin: 0;
}

.hm-ex-preview-title {
  font-size: 13px;
  color: var(--hm-font-tertiary);
  margin-top: 2px;
  display: block;
}

.hm-ex-preview-contact {
  font-size: 13px;
  color: var(--hm-font-secondary);
  margin-bottom: 12px;
}

.hm-ex-preview-block {
  margin-bottom: 12px;
}

.hm-ex-preview-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--hm-brand);
  margin-bottom: 6px;
}

.hm-ex-preview-text {
  font-size: 13px;
  color: var(--hm-font-secondary);
  line-height: 1.6;
  margin: 0;
}

.hm-ex-preview-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.hm-ex-tag {
  padding: 2px 10px;
  background: var(--hm-brand-bg-light);
  border-radius: var(--hm-radius-full);
  font-size: 12px;
  color: var(--hm-brand);
}

.hm-ex-preview-item {
  margin-bottom: 8px;
}

.hm-ex-preview-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2px;
}

.hm-ex-preview-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
}

.hm-ex-preview-item-period {
  font-size: 12px;
  color: var(--hm-font-fourth);
}

.hm-ex-export-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.hm-ex-file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-ex-file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--hm-radius-md);
  cursor: pointer;
  transition: background 0.15s;
}

.hm-ex-file-item:hover {
  background: var(--hm-hover-bg);
}

.hm-ex-file-info {
  flex: 1;
  min-width: 0;
}

.hm-ex-file-name {
  font-size: 13px;
  color: var(--hm-font-primary);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-ex-file-meta {
  font-size: 11px;
  color: var(--hm-font-fourth);
  margin-top: 2px;
  display: block;
}
</style>
