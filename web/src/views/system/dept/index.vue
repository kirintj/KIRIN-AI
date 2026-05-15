<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NPopconfirm, NTreeSelect } from 'naive-ui'

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

defineOptions({ name: '部门管理' })

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
  initForm: { order: 0 },
  doCreate: api.createDept,
  doUpdate: api.updateDept,
  doDelete: api.deleteDept,
  refresh: () => $table.value?.handleSearch(),
})

const deptOption = ref([])
const isDisabled = ref(false)

onMounted(() => {
  $table.value?.handleSearch()
  api.getDepts().then((res) => (deptOption.value = res.data))
})

const deptRules = {
  name: [
    {
      required: true,
      message: t('views.system.dept.validate_name'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

async function addDepts() {
  isDisabled.value = false
  handleAdd()
}

const columns = [
  {
    title: t('views.system.dept.col_name'),
    key: 'name',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.dept.col_remark'),
    key: 'desc',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.dept.col_actions'),
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
                if (row.parent_id === 0) {
                  isDisabled.value = true
                } else {
                  isDisabled.value = false
                }
                handleEdit(row)
              },
            },
            [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'edit'), t('views.system.dept.btn_edit')]
          ),
          [[vPermission, 'post/api/v1/dept/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ dept_id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  'button',
                  { class: 'hm-row-btn danger' },
                  [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'delete'), t('views.system.dept.btn_delete')]
                ),
                [[vPermission, 'delete/api/v1/dept/delete']]
              ),
            default: () => h('div', {}, t('views.system.dept.confirm_delete')),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer :title="t('views.system.dept.page_title')">
    <template #action>
      <div>
        <button class="hm-action-btn primary" v-permission="'post/api/v1/dept/create'" @click="addDepts">
          <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
          {{ t('views.system.dept.btn_new') }}
        </button>
      </div>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getDepts"
    >
      <template #queryBar>
        <QueryBarItem :label="t('views.system.dept.search_placeholder')" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            :placeholder="t('views.system.dept.search_placeholder')"
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
        :rules="deptRules"
      >
        <NFormItem :label="t('views.system.dept.form_parent')" path="parent_id">
          <NTreeSelect
            v-model:value="modalForm.parent_id"
            :options="deptOption"
            key-field="id"
            label-field="name"
            :placeholder="t('views.system.dept.form_parent_placeholder')"
            clearable
            default-expand-all
            :disabled="isDisabled"
          ></NTreeSelect>
        </NFormItem>
        <NFormItem :label="t('views.system.dept.form_name')" path="name">
          <NInput v-model:value="modalForm.name" clearable :placeholder="t('views.system.dept.form_name_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.system.dept.form_remark')" path="desc">
          <NInput v-model:value="modalForm.desc" type="textarea" clearable />
        </NFormItem>
        <NFormItem :label="t('views.system.dept.form_sort')" path="order">
          <NInputNumber v-model:value="modalForm.order" min="0"></NInputNumber>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
