<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NSelect, NDatePicker } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

const { t } = useI18n()

defineOptions({ name: '对话管理' })

const $table = ref(null)
const queryItems = ref({
  username: '',
  role: '',
})
const vPermission = resolveDirective('permission')

const roleOptions = [
  { label: t('views.system.chathistory.role_user'), value: 'user' },
  { label: t('views.system.chathistory.role_assistant'), value: 'assistant' },
  { label: t('views.system.chathistory.role_system'), value: 'system' },
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
  username: [{ required: true, message: t('views.system.chathistory.validate_username'), trigger: 'blur' }],
  role: [{ required: true, message: t('views.system.chathistory.validate_role'), trigger: 'blur' }],
  content: [{ required: true, message: t('views.system.chathistory.validate_content'), trigger: 'blur' }],
}

const columns = [
  { title: 'ID', key: 'id', align: 'center', width: 60 },
  { title: t('views.system.chathistory.col_username'), key: 'username', align: 'center', width: 100 },
  {
    title: t('views.system.chathistory.col_role'),
    key: 'role',
    align: 'center',
    width: 80,
    render(row) {
      const map = { user: t('views.system.chathistory.role_user'), assistant: t('views.system.chathistory.role_assistant'), system: t('views.system.chathistory.role_system') }
      return map[row.role] || row.role
    },
  },
  { title: t('views.system.chathistory.col_content'), key: 'content', align: 'left', ellipsis: { tooltip: true } },
  {
    title: t('views.system.chathistory.col_created'),
    key: 'timestamp',
    align: 'center',
    width: 180,
    render(row) {
      return row.timestamp ? formatDate(row.timestamp) : '-'
    },
  },
  {
    title: t('views.system.chathistory.col_actions'),
    key: 'actions',
    align: 'center',
    width: 140,
    fixed: 'right',
    render(row) {
      return [
        h(
          'button',
          {
            class: 'hm-row-btn',
            onClick: () => editHandle(row),
          },
          [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'edit'), t('views.system.chathistory.btn_edit')]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }),
          },
          {
            trigger: () =>
              h(
                'button',
                { class: 'hm-row-btn danger' },
                [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'delete'), t('views.system.chathistory.btn_delete')]
              ),
            default: () => t('views.system.chathistory.confirm_delete'),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer :title="t('views.system.chathistory.page_title')">
    <template #action>
      <button class="hm-action-btn primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
        {{ t('views.system.chathistory.btn_new') }}
      </button>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getChatHistoryList"
    >
      <template #queryBar>
        <QueryBarItem :label="t('views.system.chathistory.search_username')" :label-width="60">
          <NInput v-model:value="queryItems.username" clearable :placeholder="t('views.system.chathistory.search_username_placeholder')" />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.chathistory.search_role')" :label-width="40">
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
        <NFormItem :label="t('views.system.chathistory.form_username')" path="username">
          <NInput v-model:value="modalForm.username" clearable />
        </NFormItem>
        <NFormItem :label="t('views.system.chathistory.form_role')" path="role">
          <NSelect v-model:value="modalForm.role" :options="roleOptions" clearable />
        </NFormItem>
        <NFormItem :label="t('views.system.chathistory.form_content')" path="content">
          <NInput v-model:value="modalForm.content" type="textarea" :rows="4" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
