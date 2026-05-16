<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NTag,
  NTree,
  NDrawer,
  NDrawerContent,
  NTabs,
  NTabPane,
  NGrid,
  NGi,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

const { t } = useI18n()

defineOptions({ name: '角色管理' })

const roleNameMap = {
  '管理员': () => t('views.system.role.role_admin'),
  '普通用户': () => t('views.system.role.role_user'),
}

const roleDescMap = {
  '管理员角色': () => t('views.system.role.role_admin_desc'),
  '普通用户角色': () => t('views.system.role.role_user_desc'),
}

function getRoleName(name) {
  return roleNameMap[name] ? roleNameMap[name]() : name
}

function getRoleDesc(desc) {
  return roleDescMap[desc] ? roleDescMap[desc]() : desc
}

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '角色',
  initForm: {},
  doCreate: api.createRole,
  doDelete: api.deleteRole,
  doUpdate: api.updateRole,
  refresh: () => $table.value?.handleSearch(),
})

const pattern = ref('')
const menuOption = ref([]) // 菜单选项
const active = ref(false)
const menu_ids = ref([])
const role_id = ref(0)
const apiOption = ref([])
const api_ids = ref([])
const apiTree = ref([])

function buildApiTree(data) {
  const processedData = []
  const groupedData = {}

  data.forEach((item) => {
    const tags = item['tags']
    const pathParts = item['path'].split('/')
    const path = pathParts.slice(0, -1).join('/')
    const summary = tags.charAt(0).toUpperCase() + tags.slice(1)
    const unique_id = item['method'].toLowerCase() + item['path']
    if (!(path in groupedData)) {
      groupedData[path] = { unique_id: path, path: path, summary: summary, children: [] }
    }

    groupedData[path].children.push({
      id: item['id'],
      path: item['path'],
      method: item['method'],
      summary: item['summary'],
      unique_id: unique_id,
    })
  })
  processedData.push(...Object.values(groupedData))
  return processedData
}

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: t('views.system.role.col_name'),
    key: 'name',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => getRoleName(row.name) })
    },
  },
  {
    title: t('views.system.role.col_desc'),
    key: 'desc',
    width: 80,
    align: 'center',
    render(row) {
      return h('span', getRoleDesc(row.desc))
    },
  },
  {
    title: t('views.system.role.col_created'),
    key: 'created_at',
    width: 60,
    align: 'center',
    render(row) {
      return h('span', formatDate(row.created_at))
    },
  },
  {
    title: t('views.system.role.col_actions'),
    key: 'actions',
    width: 200,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            'button',
            {
              class: 'hm-row-btn',
              onClick: () => handleEdit(row),
            },
            t('views.system.role.btn_edit')
          ),
          [[vPermission, 'post/api/v1/role/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ role_id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  'button',
                  { class: 'hm-row-btn danger' },
                  t('views.system.role.btn_delete')
                ),
                [[vPermission, 'delete/api/v1/role/delete']]
              ),
            default: () => h('div', {}, t('views.system.role.confirm_delete')),
          }
        ),
        withDirectives(
          h(
            'button',
            {
              class: 'hm-row-btn',
              onClick: async () => {
                try {
                  const [menusResponse, apisResponse, roleAuthorizedResponse] = await Promise.all([
                    api.getMenus({ page: 1, page_size: 9999 }),
                    api.getApis({ page: 1, page_size: 9999 }),
                    api.getRoleAuthorized({ id: row.id }),
                  ])
                  menuOption.value = menusResponse.data
                  apiOption.value = buildApiTree(apisResponse.data)
                  menu_ids.value = roleAuthorizedResponse.data.menus.map((v) => v.id)
                  api_ids.value = roleAuthorizedResponse.data.apis.map(
                    (v) => v.method.toLowerCase() + v.path
                  )
                  active.value = true
                  role_id.value = row.id
                } catch (error) {
                  console.error('Error loading data:', error)
                }
              },
            },
            t('views.system.role.btn_set_permission')
          ),
          [[vPermission, 'get/api/v1/role/authorized']]
        ),
      ]
    },
  },
]

async function updateRoleAuthorized() {
  const checkData = apiTree.value.getCheckedData()
  const apiInfos = []
  checkData &&
    checkData.options.forEach((item) => {
      if (!item.children) {
        apiInfos.push({
          path: item.path,
          method: item.method,
        })
      }
    })
  const { code, msg } = await api.updateRoleAuthorized({
    id: role_id.value,
    menu_ids: menu_ids.value,
    api_infos: apiInfos,
  })
  if (code === 200) {
    $message?.success(t('views.system.role.msg_success'))
  } else {
    $message?.error(msg)
  }

  const result = await api.getRoleAuthorized({ id: role_id.value })
  menu_ids.value = result.data.menus.map((v) => {
    return v.id
  })
}
</script>

<template>
  <CommonPage show-footer :title="t('views.system.role.page_title')">
    <template #action>
      <button class="hm-action-btn primary" v-permission="'post/api/v1/role/create'" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
        {{ t('views.system.role.btn_new') }}
      </button>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRoleList"
    >
      <template #queryBar>
        <QueryBarItem :label="t('views.system.role.col_name')" :label-width="50">
          <NInput
            id="query-role-name"
            v-model:value="queryItems.role_name"
            clearable
            type="text"
            :placeholder="t('views.system.role.search_placeholder')"
            :aria-label="t('views.system.role.col_name')"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

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
        :disabled="modalAction === 'view'"
      >
        <NFormItem
          :label="t('views.system.role.form_name')"
          path="name"
          for="modal-role-name"
          :rule="{
            required: true,
            message: t('views.system.role.validate_name'),
            trigger: ['input', 'blur'],
          }"
        >
          <NInput id="modal-role-name" v-model:value="modalForm.name" :placeholder="t('views.system.role.form_name_placeholder')" />
        </NFormItem>
        <NFormItem :label="t('views.system.role.form_desc')" path="desc" for="modal-role-desc">
          <NInput id="modal-role-desc" v-model:value="modalForm.desc" :placeholder="t('views.system.role.form_desc_placeholder')" />
        </NFormItem>
      </NForm>
    </CrudModal>

    <NDrawer v-model:show="active" placement="right" :width="500"
      ><NDrawerContent>
        <NGrid x-gap="24" cols="12">
          <NGi span="8">
            <NInput
              id="drawer-pattern"
              v-model:value="pattern"
              type="text"
              :placeholder="t('views.system.role.filter_placeholder')"
              :aria-label="t('views.system.role.filter_placeholder')"
              style="flex-grow: 1"
            ></NInput>
          </NGi>
          <NGi offset="2">
            <NButton
              v-permission="'post/api/v1/role/authorized'"
              type="info"
              @click="updateRoleAuthorized"
              >{{ t('views.system.role.btn_confirm') }}</NButton
            >
          </NGi>
        </NGrid>
        <NTabs>
          <NTabPane name="menu" :tab="t('views.system.role.tab_menu')" display-directive="show">
            <!-- TODO：级联 -->
            <NTree
              :data="menuOption"
              :checked-keys="menu_ids"
              :pattern="pattern"
              :show-irrelevant-nodes="false"
              key-field="id"
              label-field="name"
              checkable
              :default-expand-all="true"
              :block-line="true"
              :selectable="false"
              @update:checked-keys="(v) => (menu_ids = v)"
            />
          </NTabPane>
          <NTabPane name="resource" :tab="t('views.system.role.tab_resource')" display-directive="show">
            <NTree
              ref="apiTree"
              :data="apiOption"
              :checked-keys="api_ids"
              :pattern="pattern"
              :show-irrelevant-nodes="false"
              key-field="unique_id"
              label-field="summary"
              checkable
              :default-expand-all="true"
              :block-line="true"
              :selectable="false"
              cascade
              @update:checked-keys="(v) => (api_ids = v)"
            />
          </NTabPane>
        </NTabs>
        <template #header> {{ t('views.system.role.permission_title') }} </template>
      </NDrawerContent>
    </NDrawer>
  </CommonPage>
</template>
