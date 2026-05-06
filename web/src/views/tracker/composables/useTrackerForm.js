import { ref, computed } from 'vue'
import { useTrackerStore } from '@/store/modules/tracker'

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

const SOURCE_OPTIONS = [
  { label: 'Boss直聘', value: 'Boss直聘' },
  { label: '拉勾', value: '拉勾' },
  { label: '猎聘', value: '猎聘' },
  { label: '智联招聘', value: '智联招聘' },
  { label: '内推', value: '内推' },
  { label: '官网', value: '官网' },
  { label: '其他', value: '其他' },
]

export function useTrackerForm() {
  const store = useTrackerStore()

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
    sourceOptions: SOURCE_OPTIONS,
    resetAddForm,
    handleAdd,
    openEdit,
    handleEdit,
  }
}
