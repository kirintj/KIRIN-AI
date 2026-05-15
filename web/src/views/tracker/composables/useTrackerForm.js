import { ref, computed } from 'vue'
import { useTrackerStore } from '@/store/modules/tracker'
import i18n from '~/i18n'

const t = i18n.global.t

const DEFAULT_FORM = {
  company: '',
  position: '',
  status: 'applied',
  salary: '',
  location: '',
  source: '',
  notes: '',
  contact: '',
}

export function useTrackerForm() {
  const store = useTrackerStore()

  const sourceOptions = computed(() => [
    { label: t('views.tracker.source_boss'), value: 'Boss直聘' },
    { label: t('views.tracker.source_lagou'), value: '拉勾' },
    { label: t('views.tracker.source_liepin'), value: '猎聘' },
    { label: t('views.tracker.source_zhilian'), value: '智联招聘' },
    { label: t('views.tracker.source_referral'), value: '内推' },
    { label: t('views.tracker.source_official'), value: '官网' },
    { label: t('views.tracker.source_other'), value: '其他' },
  ])

  const showAddModal = ref(false)
  const showEditModal = ref(false)
  const editingApp = ref(null)
  const addForm = ref({ ...DEFAULT_FORM })

  const statusOptions = computed(() =>
    store.STATUS_LIST.map((s) => ({ label: store.STATUS_LABELS[s], value: s }))
  )

  const resetAddForm = () => {
    addForm.value = { ...DEFAULT_FORM }
  }

  const handleAdd = async () => {
    if (!addForm.value.company || !addForm.value.position) return
    await store.createApplication(addForm.value)
    showAddModal.value = false
    resetAddForm()
  }

  const openEdit = (app) => {
    editingApp.value = { ...app }
    showEditModal.value = true
  }

  const handleEdit = async () => {
    if (!editingApp.value) return
    await store.updateApplication(editingApp.value.id, editingApp.value)
    showEditModal.value = false
    editingApp.value = null
  }

  return {
    showAddModal,
    showEditModal,
    editingApp,
    addForm,
    statusOptions,
    sourceOptions,
    resetAddForm,
    handleAdd,
    openEdit,
    handleEdit,
  }
}
