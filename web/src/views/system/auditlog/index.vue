<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NInput, NSelect, NPopover } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

const { t } = useI18n()

defineOptions({ name: '审计日志' })

const $table = ref(null)
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)

  const pad = (num) => num.toString().padStart(2, '0')

  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1) // 月份从0开始，所以需要+1
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 获取当天的开始时间的时间戳
function getStartOfDayTimestamp() {
  const now = new Date()
  now.setHours(0, 0, 0, 0) // 将小时、分钟、秒和毫秒都设置为0
  return now.getTime()
}

// 获取当天的结束时间的时间戳
function getEndOfDayTimestamp() {
  const now = new Date()
  now.setHours(23, 59, 59, 999) // 将小时设置为23，分钟设置为59，秒设置为59，毫秒设置为999
  return now.getTime()
}

const startOfDayTimestamp = getStartOfDayTimestamp()
const endOfDayTimestamp = getEndOfDayTimestamp()

queryItems.value.start_time = formatTimestamp(startOfDayTimestamp)
queryItems.value.end_time = formatTimestamp(endOfDayTimestamp)

const datetimeRange = ref([startOfDayTimestamp, endOfDayTimestamp])
const handleDateRangeChange = (value) => {
  if (value == null) {
    queryItems.value.start_time = null
    queryItems.value.end_time = null
  } else {
    queryItems.value.start_time = formatTimestamp(value[0])
    queryItems.value.end_time = formatTimestamp(value[1])
  }
}

const methodOptions = [
  {
    label: 'GET',
    value: 'GET',
  },
  {
    label: 'POST',
    value: 'POST',
  },
  {
    label: 'DELETE',
    value: 'DELETE',
  },
]

function formatJSON(data) {
  try {
    return typeof data === 'string' 
      ? JSON.stringify(JSON.parse(data), null, 2)
      : JSON.stringify(data, null, 2)
  } catch (e) {
    return data || t('views.system.auditlog.no_data')
  }
}

const columns = [
  {
    title: t('views.system.auditlog.col_username'),
    key: 'username',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_summary'),
    key: 'summary',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_module'),
    key: 'module',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_method'),
    key: 'method',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_path'),
    key: 'path',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_status'),
    key: 'status',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_body'),
    key: 'request_body',
    align: 'center',
    width: 80,
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: var(--hm-bg-container-secondary); padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.request_args)
            ),
        }
      )
    },
  },
  {
    title: t('views.system.auditlog.col_response'),
    key: 'response_body',
    align: 'center',
    width: 80,
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: var(--hm-bg-container-secondary); padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.response_body)
            ),
        }
      )
    },
  },
  {
    title: t('views.system.auditlog.col_duration'),
    key: 'response_time',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.auditlog.col_time'),
    key: 'created_at',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getAuditLogList"
    >
      <template #queryBar>
        <QueryBarItem :label="t('views.system.auditlog.search_username')" :label-width="70">
          <NInput
            v-model:value="queryItems.username"
            clearable
            type="text"
            :placeholder="t('views.system.auditlog.search_username_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.auditlog.search_module')" :label-width="70">
          <NInput
            v-model:value="queryItems.module"
            clearable
            type="text"
            :placeholder="t('views.system.auditlog.search_module_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.auditlog.search_summary')" :label-width="70">
          <NInput
            v-model:value="queryItems.summary"
            clearable
            type="text"
            :placeholder="t('views.system.auditlog.search_summary_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.auditlog.search_method')" :label-width="70">
          <NSelect
            v-model:value="queryItems.method"
            style="width: 180px"
            :options="methodOptions"
            clearable
            :placeholder="t('views.system.auditlog.search_method_placeholder')"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.auditlog.search_path')" :label-width="70">
          <NInput
            v-model:value="queryItems.path"
            clearable
            type="text"
            :placeholder="t('views.system.auditlog.search_path_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.auditlog.search_status')" :label-width="60">
          <NInput
            v-model:value="queryItems.status"
            clearable
            type="text"
            :placeholder="t('views.system.auditlog.search_status_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.auditlog.search_time')" :label-width="70">
          <NDatePicker
            v-model:value="datetimeRange"
            type="datetimerange"
            clearable
            :placeholder="t('views.system.auditlog.search_time_placeholder')"
            @update:value="handleDateRangeChange"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
