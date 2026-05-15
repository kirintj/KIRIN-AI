<template>
  <div class="hm-crud-table">
    <QueryBar v-if="$slots.queryBar" @search="handleSearch" @reset="handleReset">
      <slot name="queryBar" />
    </QueryBar>

    <div class="hm-table-card">
      <n-data-table
        :remote="remote"
        :loading="loading"
        :columns="columns"
        :data="tableData"
        :scroll-x="scrollX"
        :row-key="(row) => row[rowKey]"
        :pagination="isPagination ? pagination : false"
        @update:checked-row-keys="onChecked"
        @update:page="onPageChange"
        :theme-overrides="tableThemeOverrides"
      />
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store'

const appStore = useAppStore()

const props = defineProps({
  remote: {
    type: Boolean,
    default: true,
  },
  isPagination: {
    type: Boolean,
    default: true,
  },
  scrollX: {
    type: Number,
    default: 450,
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  columns: {
    type: Array,
    required: true,
  },
  queryItems: {
    type: Object,
    default() {
      return {}
    },
  },
  extraParams: {
    type: Object,
    default() {
      return {}
    },
  },
  getData: {
    type: Function,
    required: true,
  },
})

const tableThemeOverrides = computed(() => ({
  borderRadius: '12px',
  thColor: appStore.isDark ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
  thTextColor: 'var(--hm-font-tertiary)',
  tdColor: 'transparent',
  tdTextColor: 'var(--hm-font-primary)',
  borderColor: 'var(--hm-divider)',
  thFontWeight: '500',
}))

const emit = defineEmits(['update:queryItems', 'onChecked', 'onDataChange'])
const loading = ref(false)
const initQuery = { ...props.queryItems }
const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  pageSizes: [10, 20, 50, 100],
  showSizePicker: true,
  prefix({ itemCount }) {
    return `共 ${itemCount} 条`
  },
  onChange: (page) => {
    pagination.page = page
  },
  onUpdatePageSize: (pageSize) => {
    pagination.page_size = pageSize
    pagination.page = 1
    handleQuery()
  },
})

async function handleQuery() {
  try {
    loading.value = true
    let paginationParams = {}
    if (props.isPagination && props.remote) {
      paginationParams = { page: pagination.page, page_size: pagination.page_size }
    }
    const { data, total } = await props.getData({
      ...props.queryItems,
      ...props.extraParams,
      ...paginationParams,
    })
    tableData.value = data
    pagination.itemCount = total || 0
  } catch (error) {
    tableData.value = []
    pagination.itemCount = 0
  } finally {
    emit('onDataChange', tableData.value)
    loading.value = false
  }
}
function handleSearch() {
  pagination.page = 1
  handleQuery()
}
async function handleReset() {
  const queryItems = { ...props.queryItems }
  for (const key in queryItems) {
    queryItems[key] = null
  }
  emit('update:queryItems', { ...queryItems, ...initQuery })
  await nextTick()
  pagination.page = 1
  handleQuery()
}
function onPageChange(currentPage) {
  pagination.page = currentPage
  if (props.remote) {
    handleQuery()
  }
}
function onChecked(rowKeys) {
  if (props.columns.some((item) => item.type === 'selection')) {
    emit('onChecked', rowKeys)
  }
}

defineExpose({
  handleSearch,
  handleReset,
  tableData,
})
</script>

<style scoped>
.hm-crud-table {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hm-table-card {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  box-shadow: var(--hm-shadow-layered);
  overflow: hidden;
}
</style>
