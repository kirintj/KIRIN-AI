<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NForm, NFormItem, NInput, NPopconfirm } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import api from '@/api'

const { t } = useI18n()

defineOptions({ name: 'API管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

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
  name: 'API',
  initForm: {},
  doCreate: api.createApi,
  doUpdate: api.updateApi,
  doDelete: api.deleteApi,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
})

async function handleRefreshApi() {
  await $dialog.confirm({
    title: t('common.messages.hint'),
    type: 'warning',
    content: t('views.system.api.confirm_refresh'),
    async confirm() {
      await api.refreshApi()
      $message.success(t('views.system.api.msg_refresh_done'))
      $table.value?.handleSearch()
    },
  })
}

const addAPIRules = {
  path: [
    {
      required: true,
      message: t('views.system.api.validate_path'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  method: [
    {
      required: true,
      message: t('views.system.api.validate_method'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  summary: [
    {
      required: true,
      message: t('views.system.api.validate_desc'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  tags: [
    {
      required: true,
      message: t('views.system.api.validate_tags'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

const columns = [
  {
    title: t('views.system.api.col_path'),
    key: 'path',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.api.col_method'),
    key: 'method',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.api.col_desc'),
    key: 'summary',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Tags',
    key: 'tags',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.api.col_actions'),
    key: 'actions',
    width: 140,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            'button',
            {
              class: 'hm-row-btn',
              onClick: () => {
                handleEdit(row)
                modalForm.value.roles = row.roles.map((e) => (e = e.id))
              },
            },
            [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'edit'), t('views.system.api.btn_edit')]
          ),
          [[vPermission, 'post/api/v1/api/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ api_id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  'button',
                  { class: 'hm-row-btn danger' },
                  [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'delete'), t('views.system.api.btn_delete')]
                ),
                [[vPermission, 'delete/api/v1/api/delete']]
              ),
            default: () => h('div', {}, t('views.system.api.confirm_delete')),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer :title="t('views.system.api.page_title')">
    <template #action>
      <div class="hm-action-group">
        <button class="hm-action-btn" v-permission="'post/api/v1/api/refresh'" @click="handleRefreshApi">
          <TheIcon icon="material-symbols:refresh" :size="16" />
          {{ t('views.system.api.btn_refresh') }}
        </button>
        <button class="hm-action-btn primary" v-permission="'post/api/v1/api/create'" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
          {{ t('views.system.api.btn_new') }}
        </button>
      </div>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getApis"
    >
      <template #queryBar>
        <QueryBarItem :label="t('views.system.api.label_path')" :label-width="40">
          <NInput
            v-model:value="queryItems.path"
            clearable
            type="text"
            :placeholder="t('views.system.api.search_path_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem :label="t('views.system.api.label_desc')" :label-width="70">
          <NInput
            v-model:value="queryItems.summary"
            clearable
            type="text"
            :placeholder="t('views.system.api.search_desc_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="Tags" :label-width="40">
          <NInput
            v-model:value="queryItems.tags"
            clearable
            type="text"
            :placeholder="t('views.system.api.search_module_placeholder')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="addAPIRules"
      >
        <NFormItem :label="t('views.system.api.form_name')" path="path">
          <NInput v-model:value="modalForm.path" clearable :placeholder="t('views.system.api.form_name_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.system.api.form_method')" path="method">
          <NInput v-model:value="modalForm.method" clearable :placeholder="t('views.system.api.form_method_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.system.api.form_desc')" path="summary">
          <NInput v-model:value="modalForm.summary" clearable :placeholder="t('views.system.api.form_desc_placeholder')" />
        </NFormItem>
        <NFormItem label="Tags" path="tags">
          <NInput v-model:value="modalForm.tags" clearable :placeholder="t('views.system.api.form_tags_placeholder')" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
