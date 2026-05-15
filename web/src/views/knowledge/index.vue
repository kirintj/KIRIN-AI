<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { NButton, NInput, NPopconfirm, NUpload, NText, NSelect, NModal } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { useFileUpload, validateDocumentFile } from '@/composables/useFileUpload'
import { useMarkdown } from '@/composables/useMarkdown'

defineOptions({ name: '知识库管理' })

const docContent = ref('')
const docLoading = ref(false)
const clearLoading = ref(false)
const fileList = ref([])
const selectedCollection = ref('knowledge_base')
const selectedDocType = ref('')
const statsLoading = ref(false)
const searchKeyword = ref('')
const selectedDocIds = ref<Set<string>>(new Set())
const showPreview = ref(false)
const previewContent = ref('')
const previewTitle = ref('')
const browseTab = ref<'upload' | 'browse'>('upload')
const docList = ref<any[]>([])
const docListTotal = ref(0)
const docListPage = ref(1)
const docListPageSize = ref(10)
const docListLoading = ref(false)
const showDocDetail = ref(false)
const docDetailData = ref<any>(null)
const docDetailLoading = ref(false)
const currentChunkPage = ref(1)
const { uploading: uploadLoading, uploadToKnowledgeBase } = useFileUpload()
const { formatMarkdown } = useMarkdown()

const collectionOptions = [
  { label: '通用知识库', value: 'knowledge_base' },
  { label: '简历库', value: 'resume' },
  { label: '面试题库', value: 'activity-source' },
  { label: '薪资报告', value: 'salary' },
  { label: '求职攻略', value: 'map-draw' },
]

const docTypeOptions = [
  { label: '不指定', value: '' },
  { label: '简历', value: 'resume' },
  { label: '面试题', value: 'activity-source' },
  { label: '薪资报告', value: 'salary' },
  { label: '攻略文档', value: 'map-draw' },
  { label: '企业文化', value: 'company_culture' },
  { label: '岗位要求', value: 'job_requirement' },
]

const collectionStats = ref<Record<string, { count: number }>>({})

const loadStats = async () => {
  statsLoading.value = true
  try {
    const res = await api.getDocumentStats()
    collectionStats.value = res.data || {}
  } catch (error) {
    console.error('加载统计失败', error)
  } finally {
    statsLoading.value = false
  }
}

const handleAddDocument = async () => {
  if (!docContent.value.trim()) return
  docLoading.value = true
  try {
    const documents = docContent.value
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
    if (documents.length === 0) {
      window.$message?.warning('请输入有效的文档内容')
      return
    }
    await api.addDocuments({
      documents,
      collection_name: selectedCollection.value,
      doc_type: selectedDocType.value,
    })
    window.$message?.success(`成功添加 ${documents.length} 条文档到 [${getCollectionLabel(selectedCollection.value)}]`)
    docContent.value = ''
    await loadStats()
    if (browseTab.value === 'browse') loadDocList()
  } catch (error: any) {
    const msg = error?.message || error?.msg || '添加文档失败'
    window.$message?.error(msg)
  } finally {
    docLoading.value = false
  }
}

const handleClearDocuments = async () => {
  clearLoading.value = true
  try {
    await api.clearDocuments({ collection_name: selectedCollection.value })
    window.$message?.success(`集合 [${selectedCollection.value}] 已清空`)
    await loadStats()
  } catch (error) {
    console.error('清空知识库失败', error)
  } finally {
    clearLoading.value = false
  }
}

let statsReloadTimer: ReturnType<typeof setTimeout> | null = null
const debouncedLoadStats = () => {
  if (statsReloadTimer) clearTimeout(statsReloadTimer)
  statsReloadTimer = setTimeout(() => {
    loadStats()
    if (browseTab.value === 'browse') loadDocList()
  }, 500)
}

const handleUpload = async ({ file, onFinish, onError }: any) => {
  const nativeFile = file.file
  if (!nativeFile) {
    onError()
    return false
  }
  const result = await uploadToKnowledgeBase(nativeFile, selectedCollection.value, selectedDocType.value)
  if (result) {
    debouncedLoadStats()
    onFinish()
    return true
  }
  onError()
  return false
}

const handleBeforeUpload = (data: any) => {
  const fileInfo = data.file || data
  const nativeFile = fileInfo.file || fileInfo
  return validateDocumentFile(nativeFile)
}

const getCollectionLabel = (key: string) => {
  const found = collectionOptions.find((o) => o.value === key)
  return found ? found.label : key
}

const totalDocs = () => {
  return Object.values(collectionStats.value).reduce((sum, s) => sum + (s.count || 0), 0)
}

const statItems = ref<{ key: string; label: string; count: number; color: string; icon: string }[]>([])

const updateStatItems = () => {
  const colors: Record<string, string> = {
    knowledge_base: '#0A59F7',
    resume: '#722ED1',
    'activity-source': '#ED6F21',
    salary: '#64BB5C',
    'map-draw': '#E84026',
  }
  const icons: Record<string, string> = {
    _total: 'icon-park-outline:data-file',
    knowledge_base: 'icon-park-outline:data',
    resume: 'icon-park-outline:clipboard',
    'activity-source': 'icon-park-outline:activity-source',
    salary: 'icon-park-outline:finance',
    'map-draw': 'icon-park-outline:map-draw',
  }
  const items = [{ key: '_total', label: '总文档', count: totalDocs(), color: '#0A59F7', icon: icons._total }]
  for (const [key, val] of Object.entries(collectionStats.value)) {
    items.push({ key, label: getCollectionLabel(key), count: val.count || 0, color: colors[key] || '#86909C', icon: icons[key] || 'icon-park-outline:file' })
  }
  statItems.value = items
}

const guides = [
  { icon: 'icon-park-outline:data', title: '多集合管理', desc: '知识库分为通用、简历、面试、薪资、攻略五个集合，上传文档时可选择目标集合', color: '#0A59F7' },
  { icon: 'icon-park-outline:edit', title: '添加文档', desc: '在输入框中输入文档内容，每行一条，点击添加即可存入指定集合', color: '#722ED1' },
  { icon: 'material-symbols:upload', title: '上传文件', desc: '支持 PDF/DOCX/TXT/MD 等格式，系统自动提取内容并分块存入指定集合', color: '#ED6F21' },
  { icon: 'icon-park-outline:link-two', title: 'RAG 检索溯源', desc: '求职助手各功能会自动从对应集合检索文档，结果附带来源标注', color: '#64BB5C' },
  { icon: 'icon-park-outline:like', title: '反馈优化', desc: '用户可对检索结果评分反馈，低评分反馈用于优化检索策略和补充文档库', color: '#E84026' },
]

const collectionCards = computed(() => {
  const colors: Record<string, string> = {
    knowledge_base: '#0A59F7',
    resume: '#722ED1',
    'activity-source': '#ED6F21',
    salary: '#64BB5C',
    'map-draw': '#E84026',
  }
  const icons: Record<string, string> = {
    knowledge_base: 'icon-park-outline:data',
    resume: 'icon-park-outline:clipboard',
    'activity-source': 'icon-park-outline:activity-source',
    salary: 'icon-park-outline:finance',
    'map-draw': 'icon-park-outline:map-draw',
  }
  return collectionOptions.map((opt) => {
    const stat = collectionStats.value[opt.value]
    return {
      key: opt.value,
      label: opt.label,
      count: stat?.count || 0,
      color: colors[opt.value] || '#86909C',
      icon: icons[opt.value] || 'icon-park-outline:data',
      active: selectedCollection.value === opt.value,
    }
  })
})

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) return
  try {
    previewTitle.value = `搜索结果：${searchKeyword.value}`
    previewContent.value = `正在搜索 "${searchKeyword.value}" ...`
    showPreview.value = true
    const res = await api.searchDocuments({
      query: searchKeyword.value,
      collection_name: selectedCollection.value,
    })
    const results = res.data?.results || res.data || []
    if (results.length === 0) {
      previewContent.value = '未找到匹配的文档'
    } else {
      previewContent.value = results.map((r: any, i: number) =>
        `### 结果 ${i + 1}\n${r.content || r.text || JSON.stringify(r)}`
      ).join('\n\n---\n\n')
    }
  } catch (error) {
    previewContent.value = '搜索失败，请重试'
    console.error('搜索失败', error)
  }
}

const openPreview = (collectionKey: string) => {
  previewTitle.value = getCollectionLabel(collectionKey)
  previewContent.value = `集合 [${getCollectionLabel(collectionKey)}] 共有 ${collectionStats.value[collectionKey]?.count || 0} 条文档`
  showPreview.value = true
}

const toggleDocSelect = (docId: string) => {
  if (selectedDocIds.value.has(docId)) {
    selectedDocIds.value.delete(docId)
  } else {
    selectedDocIds.value.add(docId)
  }
}

const handleBatchDelete = async () => {
  if (selectedDocIds.value.size === 0) return
  try {
    window.$message?.success(`已选择 ${selectedDocIds.value.size} 条文档`)
    selectedDocIds.value.clear()
    await loadStats()
  } catch (error) {
    console.error('批量操作失败', error)
  }
}

const loadDocList = async () => {
  docListLoading.value = true
  try {
    const res = await api.listDocuments({
      collection_name: selectedCollection.value,
      page: docListPage.value,
      page_size: docListPageSize.value,
      doc_type: selectedDocType.value,
    })
    const data = res.data || {}
    docList.value = data.documents || []
    docListTotal.value = data.total || 0
  } catch (error) {
    console.error('加载文档列表失败', error)
    docList.value = []
    docListTotal.value = 0
  } finally {
    docListLoading.value = false
  }
}

const loadDocDetail = async (docId: string) => {
  docDetailLoading.value = true
  showDocDetail.value = true
  docDetailData.value = null
  currentChunkPage.value = 1
  try {
    const res = await api.getDocumentDetail({
      doc_id: docId,
      collection_name: selectedCollection.value,
    })
    docDetailData.value = res.data || null
  } catch (error) {
    console.error('加载文档详情失败', error)
    docDetailData.value = null
  } finally {
    docDetailLoading.value = false
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(docListTotal.value / docListPageSize.value)))

const chunkTotal = computed(() => docDetailData.value?.chunks?.length || 0)
const currentChunk = computed(() => {
  const chunks = docDetailData.value?.chunks
  if (!chunks || chunks.length === 0) return null
  return chunks[currentChunkPage.value - 1] || null
})

const handlePageChange = (page: number) => {
  docListPage.value = page
  loadDocList()
}

watch(browseTab, (val) => {
  if (val === 'browse') loadDocList()
})

watch(selectedCollection, () => {
  if (browseTab.value === 'browse') {
    docListPage.value = 1
    loadDocList()
  }
})

onMounted(async () => {
  await loadStats()
  updateStatItems()
})

watch(collectionStats, () => updateStatItems(), { deep: true })
</script>

<template>
  <AppPage :show-footer="false">
    <div class="hm-page-container">
      <div class="hm-page-header">
        <div>
          <h1 class="hm-page-title">知识库管理</h1>
          <p class="hm-page-subtitle">文档管理 · 向量化 · RAG 检索</p>
        </div>
        <div class="hm-kn-actions">
          <button class="hm-action-btn" @click="loadStats" :disabled="statsLoading">
            <TheIcon icon="icon-park-outline:refresh" :size="16" />
          </button>
          <NPopconfirm @positive-click="handleClearDocuments">
            <template #trigger>
              <button class="hm-action-btn danger">
                <TheIcon icon="icon-park-outline:delete" :size="16" />
                <span class="hm-btn-text">清空当前集合</span>
              </button>
            </template>
            确定要清空集合 [{{ getCollectionLabel(selectedCollection) }}] 的所有文档吗？此操作不可恢复。
          </NPopconfirm>
        </div>
      </div>

      <div class="hm-stats-row">
        <div v-for="stat in statItems" :key="stat.key" class="hm-stat-card">
          <div class="hm-stat-icon" :style="{ background: stat.color + '14' }">
            <TheIcon :icon="stat.icon" :size="20" :color="stat.color" />
          </div>
          <div class="hm-stat-info">
            <div class="hm-stat-value" :style="{ color: stat.color }">{{ stat.count }}</div>
            <div class="hm-stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>

      <div class="hm-section">
        <h2 class="hm-section-title">文档搜索</h2>
        <div class="hm-search-bar">
          <div class="hm-search-box" style="flex: 1; padding: 10px 16px;">
            <TheIcon icon="icon-park-outline:search" :size="16" color="var(--hm-font-fourth)" />
            <input v-model="searchKeyword" class="hm-search-input" style="font-size: 14px;" placeholder="输入关键词搜索文档..."
              @keydown.enter="handleSearch" />
            <button v-if="searchKeyword" class="hm-search-clear" @click="searchKeyword = ''">
              <TheIcon icon="icon-park-outline:close" :size="12" />
            </button>
          </div>
          <button class="hm-action-btn primary" @click="handleSearch" :disabled="!searchKeyword.trim()">
            <TheIcon icon="icon-park-outline:search" :size="14" color="#fff" />
            搜索
          </button>
        </div>
      </div>

      <div class="hm-section">
        <h2 class="hm-section-title">集合概览</h2>
        <div class="hm-collection-grid">
          <div v-for="card in collectionCards" :key="card.key" :class="['hm-collection-card', { active: card.active }]"
            @click="selectedCollection = card.key">
            <div class="hm-collection-icon" :style="{ background: card.color + '14' }">
              <TheIcon :icon="card.icon" :size="24" :color="card.color" />
            </div>
            <div class="hm-collection-info">
              <div class="hm-collection-label">{{ card.label }}</div>
              <div class="hm-collection-count">{{ card.count }} 条文档</div>
            </div>
            <button class="hm-collection-preview" @click.stop="openPreview(card.key)">
              <TheIcon icon="icon-park-outline:preview-open" :size="14" color="var(--hm-font-fourth)" />
            </button>
          </div>
        </div>
      </div>

      <div class="hm-section">
        <div class="hm-tab-bar">
          <button :class="['hm-tab-item', { active: browseTab === 'upload' }]" @click="browseTab = 'upload'">
            <TheIcon icon="icon-park-outline:upload" :size="16" />
            上传管理
          </button>
          <button :class="['hm-tab-item', { active: browseTab === 'browse' }]" @click="browseTab = 'browse'">
            <TheIcon icon="icon-park-outline:preview-open" :size="16" />
            浏览文档
          </button>
        </div>

        <template v-if="browseTab === 'upload'">
          <div class="hm-section-inner">
            <div class="hm-selector-row">
              <div class="hm-selector-item">
                <label class="hm-selector-label">文档集合</label>
                <NSelect v-model:value="selectedCollection" :options="collectionOptions" size="small"
                  style="width: 180px" />
              </div>
              <div class="hm-selector-item">
                <label class="hm-selector-label">文档类型</label>
                <NSelect v-model:value="selectedDocType" :options="docTypeOptions" size="small" style="width: 180px" />
              </div>
            </div>

        <h3 class="hm-sub-title">上传文件</h3>
            <div class="hm-upload-form">
              <NUpload v-model:file-list="fileList" :before-upload="handleBeforeUpload" :custom-request="handleUpload"
                :max="5" :multiple="true" :disabled="uploadLoading">
                <button class="hm-upload-btn">
                  <TheIcon icon="material-symbols:upload" :size="20" color="var(--hm-brand)" />
                  <span>选择文件上传</span>
                </button>
              </NUpload>
              <p class="hm-upload-tip">
                支持 PDF、DOCX、TXT、MD 等文件，单个不超过 10MB，上传到 [{{ getCollectionLabel(selectedCollection) }}] 集合
              </p>
            </div>

            <h3 class="hm-sub-title">添加文档</h3>
            <div class="hm-doc-form">
              <NInput v-model:value="docContent" type="textarea" placeholder="输入文档内容，每行一条文档..." :rows="6"
                :disabled="docLoading" />
              <div class="hm-doc-actions">
                <span class="hm-doc-target">目标集合：{{ getCollectionLabel(selectedCollection) }}</span>
                <button class="hm-action-btn primary" :disabled="!docContent.trim()" @click="handleAddDocument">
                  <TheIcon v-if="!docLoading" icon="icon-park-outline:add" :size="16" color="#fff" />
                  {{ docLoading ? '添加中...' : '添加到知识库' }}
                </button>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="hm-section-inner">
            <div class="hm-browse-header">
              <div class="hm-browse-info">
                当前集合：<strong>{{ getCollectionLabel(selectedCollection) }}</strong>
                <span class="hm-browse-total">共 {{ docListTotal }} 篇文档</span>
              </div>
              <button class="hm-action-btn" @click="loadDocList" :disabled="docListLoading">
                <TheIcon icon="icon-park-outline:refresh" :size="14" />
                刷新
              </button>
            </div>

            <div v-if="docListLoading" class="hm-browse-skeleton">
              <div v-for="i in 5" :key="i" class="hm-skeleton hm-skeleton-text long"></div>
            </div>

            <div v-else-if="docList.length === 0" class="hm-empty-state">
              <div class="hm-empty-state-icon">
                <TheIcon icon="icon-park-outline:data" :size="32" color="var(--hm-font-fourth)" />
              </div>
              <div class="hm-empty-state-title">暂无文档</div>
              <div class="hm-empty-state-desc">切换到"上传管理"标签页添加文档</div>
            </div>

            <div v-else class="hm-doc-list">
              <div v-for="doc in docList" :key="doc.doc_id" class="hm-doc-item" @click="loadDocDetail(doc.doc_id)">
                <div class="hm-doc-item-icon">
                  <TheIcon icon="icon-park-outline:file-text" :size="20" color="var(--hm-brand)" />
                </div>
                <div class="hm-doc-item-info">
                  <div class="hm-doc-item-id">{{ doc.source || doc.doc_id }}</div>
                  <div class="hm-doc-item-preview">{{ doc.preview }}</div>
                </div>
                <div class="hm-doc-item-meta">
                  <span v-if="doc.doc_type" class="hm-doc-type-tag">{{ doc.doc_type }}</span>
                  <span class="hm-doc-chunk-count">{{ doc.chunk_count }} 块</span>
                </div>
                <TheIcon icon="icon-park-outline:right" :size="14" color="var(--hm-font-fourth)" />
              </div>
            </div>

            <div v-if="docListTotal > docListPageSize" class="hm-pagination">
              <button class="hm-page-btn" :disabled="docListPage <= 1"
                @click="handlePageChange(docListPage - 1)">上一页</button>
              <span class="hm-page-info">{{ docListPage }} / {{ totalPages }}</span>
              <button class="hm-page-btn" :disabled="docListPage >= totalPages"
                @click="handlePageChange(docListPage + 1)">下一页</button>
            </div>
          </div>
        </template>
      </div>

      <div class="hm-section">
        <h2 class="hm-section-title">使用说明</h2>
        <div class="hm-guide-list">
          <div v-for="g in guides" :key="g.title" class="hm-guide-item">
            <div class="hm-guide-icon" :style="{ background: g.color + '14' }">
              <TheIcon :icon="g.icon" :size="20" :color="g.color" />
            </div>
            <div class="hm-guide-info">
              <div class="hm-guide-title">{{ g.title }}</div>
              <div class="hm-guide-desc">{{ g.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <NModal v-model:show="showPreview" preset="card" :title="previewTitle" style="width: 600px">
        <div class="hm-preview-content md-bubble" v-html="formatMarkdown(previewContent)"></div>
        <template #footer>
          <button class="hm-action-btn" @click="showPreview = false">关闭</button>
        </template>
      </NModal>

      <NModal v-model:show="showDocDetail" preset="card"
        :title="docDetailData ? `文档详情 - ${docDetailData.doc_id}` : '文档详情'" style="width: 760px">
        <div v-if="docDetailLoading" class="hm-browse-skeleton">
          <div v-for="i in 3" :key="i" class="hm-skeleton hm-skeleton-text long"></div>
        </div>
        <div v-else-if="docDetailData" class="hm-doc-detail">
          <div class="hm-doc-detail-meta">
            <span>共 {{ chunkTotal }} 个分块</span>
          </div>
          <div v-if="currentChunk" class="hm-doc-chunk">
            <div class="hm-doc-chunk-header">
              <span class="hm-doc-chunk-index">分块 #{{ currentChunk.chunk_index }}</span>
              <span v-if="currentChunk.doc_type" class="hm-doc-type-tag">{{ currentChunk.doc_type }}</span>
            </div>
            <div class="hm-doc-chunk-content">{{ currentChunk.content }}</div>
          </div>
          <div v-if="chunkTotal > 1" class="hm-chunk-pagination">
            <button class="hm-page-btn" :disabled="currentChunkPage <= 1" @click="currentChunkPage--">上一个</button>
            <div class="hm-chunk-page-jump">
              <input v-model.number="currentChunkPage" type="number" :min="1" :max="chunkTotal"
                class="hm-chunk-page-input"
                @change="currentChunkPage = Math.max(1, Math.min(chunkTotal, currentChunkPage))" />
              <span class="hm-chunk-page-total">/ {{ chunkTotal }}</span>
            </div>
            <button class="hm-page-btn" :disabled="currentChunkPage >= chunkTotal"
              @click="currentChunkPage++">下一个</button>
          </div>
        </div>
        <div v-else class="hm-empty-state">
          <div class="hm-empty-state-title">无法加载文档详情</div>
        </div>
        <template #footer>
          <button class="hm-action-btn" @click="showDocDetail = false">关闭</button>
        </template>
      </NModal>
    </div>
  </AppPage>
</template>

<style scoped>
.hm-knowledge-page {
  width: 100%;
  margin: 0 auto;
  padding: 32px 28px;
}

.hm-kn-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding: 24px 28px;
  border-radius: var(--hm-radius-xl);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass-strong);
  -webkit-backdrop-filter: var(--hm-blur-glass-strong);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered), 0 8px 24px var(--hm-brand-bg-light);
}

.hm-kn-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
}

.hm-kn-subtitle {
  font-size: 14px;
  color: var(--hm-font-tertiary);
}

.hm-kn-actions {
  display: flex;
  gap: 8px;
}

.hm-stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 28px;
}

.hm-stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  transition: all 0.35s var(--hm-spring);
}

.hm-stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--hm-shadow-layered-hover);
}

.hm-stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.hm-stat-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.3px;
}

.hm-stat-label {
  font-size: 12px;
  color: var(--hm-font-tertiary);
  margin-top: 2px;
  font-weight: 500;
}

.hm-section {
  margin-bottom: 28px;
}

.hm-section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--hm-font-primary);
  margin-bottom: 14px;
  letter-spacing: -0.2px;
}

.hm-search-bar {
  display: flex;
  gap: 10px;
  align-items: center;
}

.hm-search-input-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  transition: all 0.3s var(--hm-spring);
}

.hm-search-input-box:focus-within {
  border-color: var(--hm-brand);
  box-shadow: var(--hm-focus-ring);
}

.hm-search-field {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--hm-font-primary);
  font-family: inherit;
}

.hm-search-field::placeholder {
  color: var(--hm-font-fourth);
}

.hm-search-clear {
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-fourth);
  transition: all 0.15s;
}

.hm-search-clear:hover {
  background: var(--hm-pressed-bg);
}

.hm-main-layout {
  display: flex;
  gap: 20px;
  min-height: 500px;
}

.hm-left-panel {
  width: 340px;
  flex-shrink: 0;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hm-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--hm-divider);
}

.hm-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-panel-actions {
  display: flex;
  gap: 6px;
}

.hm-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  cursor: pointer;
  color: var(--hm-font-tertiary);
  transition: all 0.25s var(--hm-spring);
}

.hm-icon-btn:hover {
  background: var(--hm-hover-bg);
  color: var(--hm-font-primary);
  transform: scale(1.1);
}

.hm-icon-btn.active {
  background: var(--hm-brand-light);
  color: var(--hm-brand);
}

.hm-icon-btn.danger:hover {
  background: var(--hm-danger-hover-bg);
  color: var(--hm-error);
}

.hm-collection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.hm-collection-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-collection-card:hover {
  border-color: var(--hm-brand);
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-3px);
}

.hm-collection-card.active {
  border-color: var(--hm-brand);
  background: var(--hm-brand-light);
}

.hm-collection-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--hm-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hm-collection-info {
  flex: 1;
  min-width: 0;
}

.hm-collection-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
}

.hm-collection-count {
  font-size: 12px;
  color: var(--hm-font-tertiary);
  margin-top: 2px;
}

.hm-collection-preview {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
  flex-shrink: 0;
}

.hm-collection-preview:hover {
  background: var(--hm-hover-bg);
  transform: scale(1.1);
}

.hm-preview-content {
  max-height: 400px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.7;
  color: var(--hm-font-primary);
}


.hm-section-inner {
  padding: 0 4px;
}

.hm-sub-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
  margin: 20px 0 12px;
}

.hm-browse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.hm-browse-info {
  font-size: 14px;
  color: var(--hm-font-secondary);
}

.hm-browse-total {
  margin-left: 8px;
  font-size: 12px;
  color: var(--hm-font-fourth);
}

.hm-browse-skeleton {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 0;
}

.hm-doc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hm-doc-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--hm-radius-md);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
}

.hm-doc-item:hover {
  background: var(--hm-brand-bg-light);
  transform: translateX(2px);
}

.hm-doc-item.active {
  background: var(--hm-brand-light);
}

.hm-doc-item-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--hm-radius-md);
  background: var(--hm-brand-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.3s var(--hm-spring);
}

.hm-doc-item:hover .hm-doc-item-icon {
  transform: scale(1.08);
}

.hm-doc-item-info {
  flex: 1;
  min-width: 0;
}

.hm-doc-item-id {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-doc-item-preview {
  font-size: 12px;
  color: var(--hm-font-tertiary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-doc-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.hm-doc-type-tag {
  padding: 2px 8px;
  border-radius: var(--hm-radius-sm);
  background: rgba(114, 46, 209, 0.08);
  color: #722ED1;
  font-size: 11px;
  font-weight: 500;
}

.hm-doc-chunk-count {
  font-size: 12px;
  color: var(--hm-font-fourth);
}

.hm-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--hm-divider);
}

.hm-page-btn {
  padding: 6px 14px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  font-size: 13px;
  color: var(--hm-font-primary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-page-btn:hover:not(:disabled) {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  transform: translateY(-1px);
  box-shadow: var(--hm-shadow-brand);
}

.hm-page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.hm-page-info {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}

.hm-doc-detail-meta {
  font-size: 13px;
  color: var(--hm-font-tertiary);
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--hm-divider);
}

.hm-chunk-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--hm-divider);
}

.hm-chunk-page-jump {
  display: flex;
  align-items: center;
  gap: 4px;
}

.hm-chunk-page-input {
  width: 48px;
  height: 28px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-sm);
  text-align: center;
  font-size: 13px;
  color: var(--hm-font-primary);
  background: var(--hm-bg-secondary);
}

.hm-chunk-page-input:focus {
  outline: none;
  border-color: var(--hm-brand);
}

.hm-chunk-page-total {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}

.hm-doc-chunks {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hm-doc-chunk {
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-md);
  overflow: hidden;
}

.hm-doc-chunk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--hm-bg-container-secondary);
  border-bottom: 1px solid var(--hm-border);
}

.hm-doc-chunk-index {
  font-size: 12px;
  font-weight: 500;
  color: var(--hm-font-secondary);
}

.hm-doc-chunk-content {
  padding: 12px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--hm-font-primary);
  white-space: pre-wrap;
  word-break: break-all;
}

.hm-selector-row {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.hm-selector-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hm-selector-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-secondary);
  white-space: nowrap;
}

.hm-doc-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hm-doc-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hm-doc-target {
  font-size: 13px;
  color: var(--hm-font-tertiary);
}

.hm-upload-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hm-upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 24px;
  border: 2px dashed var(--hm-border);
  border-radius: var(--hm-radius-xl);
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  font-size: 14px;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-upload-btn:hover {
  border-color: var(--hm-brand);
  background: var(--hm-brand-light);
  transform: translateY(-2px);
  box-shadow: var(--hm-shadow-brand);
}

.hm-upload-tip {
  font-size: 12px;
  color: var(--hm-font-fourth);
}

.hm-guide-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hm-guide-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  box-shadow: var(--hm-shadow-layered);
  transition: all 0.3s var(--hm-spring);
}

.hm-guide-item:hover {
  box-shadow: var(--hm-shadow-layered-hover);
  transform: translateY(-3px);
}

.hm-guide-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--hm-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hm-guide-info {
  flex: 1;
  min-width: 0;
}

.hm-guide-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-primary);
  margin-bottom: 2px;
}

.hm-guide-desc {
  font-size: 13px;
  color: var(--hm-font-tertiary);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .hm-knowledge-page {
    padding: 16px 12px;
  }

  .hm-kn-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 16px;
    gap: 12px;
  }

  .hm-kn-header-right {
    width: 100%;
    justify-content: space-between;
  }

  .hm-kn-title {
    font-size: 22px;
  }

  .hm-stats-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .hm-stat-card {
    padding: 12px;
  }

  .hm-stat-icon {
    width: 36px;
    height: 36px;
  }

  .hm-stat-value {
    font-size: 20px;
  }

  .hm-selector-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .hm-doc-item {
    padding: 10px 12px;
  }

  .hm-doc-item-icon {
    width: 34px;
    height: 34px;
  }

  .hm-doc-item-meta {
    flex-direction: column;
    gap: 2px;
  }

  .hm-guide-item {
    padding: 12px 14px;
  }

  .hm-guide-icon {
    width: 34px;
    height: 34px;
  }

  .hm-browse-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .hm-kn-actions {
    width: 100%;
    order: 3;
  }

  .hm-kn-actions .hm-btn-text {
    display: none;
  }

  .hm-kn-actions .hm-action-btn {
    padding: 6px 10px;
    font-size: 12px;
  }

  .hm-search-bar {
    flex-direction: column;
    gap: 8px;
  }

  .hm-search-bar .hm-action-btn {
    width: 100%;
    justify-content: center;
  }

  .hm-upload-btn {
    padding: 16px;
    font-size: 13px;
  }

  .hm-chunk-pagination {
    flex-wrap: wrap;
    gap: 8px;
  }

  .hm-chunk-page-input {
    width: 40px;
  }
}

@media (max-width: 480px) {
  .hm-stats-row {
    grid-template-columns: 1fr;
  }

  .hm-doc-item-preview {
    display: none;
  }

  .hm-kn-actions .hm-action-btn {
    font-size: 12px;
    padding: 7px 10px;
  }

  .hm-chunk-pagination .hm-page-btn {
    padding: 5px 10px;
    font-size: 12px;
  }
}
</style>
