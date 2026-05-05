<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NSelect, NDatePicker } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '对话管理' })

const $table = ref(null)
const queryItems = ref({
  username: '',
  role: '',
})
const vPermission = resolveDirective('permission')

const roleOptions = [
  { label: '用户', value: 'user' },
  { label: '助手', value: 'assistant' },
  { label: '系统', value: 'system' },
]

const formatValidDate = (date) => {
  if (!date) return new Date()
  if (date instanceof Date) return date
  const parsedDate = new Date(date)
  return isNaN(parsedDate.getTime()) ? new Date() : parsedDate
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: 'ChatHistory',
  initForm: {
    username: '',
    role: '',
    content: '',
    timestamp: new Date(),
  },
  doCreate: api.createChatHistory,
  doUpdate: api.updateChatHistory,
  doDelete: api.deleteChatHistory,
  refresh: () => $table.value?.handleSearch(),
})

const editHandle = (row) => {
  row.timestamp = formatValidDate(row.timestamp)
  handleEdit(row)
}

onMounted(() => {
  $table.value?.handleSearch()
})

const addChatRules = {
  username: [{ required: true, message: '请输入用户名称', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'blur' }],
  content: [{ required: true, message: '请输入消息内容', trigger: 'blur' }],
}

const columns = [
  { title: 'ID', key: 'id', align: 'center', width: 60 },
  { title: '用户名称', key: 'username', align: 'center', width: 100 },
  {
    title: '角色',
    key: 'role',
    align: 'center',
    width: 80,
    render(row) {
      const map = { user: '用户', assistant: '助手', system: '系统' }
      return map[row.role] || row.role
    },
  },
  { title: '消息内容', key: 'content', align: 'left', ellipsis: { tooltip: true } },
  {
    title: '创建时间',
    key: 'timestamp',
    align: 'center',
    width: 180,
    render(row) {
      return row.timestamp ? formatDate(row.timestamp) : '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    align: 'center',
    width: 140,
    fixed: 'right',
    render(row) {
      return [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            onClick: () => editHandle(row),
          },
          {
            default: () => '编辑',
            icon: renderIcon('material-symbols:edit', { size: 16 }),
          }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
          },
          {
            trigger: () =>
              h(
                NButton,
                { size: 'small', type: 'error' },
                {
                  default: () => '删除',
                  icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                }
              ),
            default: () => '确定删除该记录？',
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="对话记录列表">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建记录
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getChatHistoryList"
    >
      <template #queryBar>
        <QueryBarItem label="用户名" :label-width="60">
          <NInput v-model:value="queryItems.username" clearable placeholder="用户名" />
        </QueryBarItem>
        <QueryBarItem label="角色" :label-width="40">
          <NSelect v-model:value="queryItems.role" clearable :options="roleOptions" />
        </QueryBarItem>
      </template>
    </CrudTable>

    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm ref="modalFormRef" :model="modalForm" :rules="addChatRules" label-width="80">
        <NFormItem label="用户名称" path="username">
          <NInput v-model:value="modalForm.username" clearable />
        </NFormItem>
        <NFormItem label="角色" path="role">
          <NSelect v-model:value="modalForm.role" :options="roleOptions" clearable />
        </NFormItem>
        <NFormItem label="内容" path="content">
          <NInput v-model:value="modalForm.content" type="textarea" :rows="4" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
