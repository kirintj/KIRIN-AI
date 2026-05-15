<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSwitch,
  NTreeSelect,
  NRadio,
  NRadioGroup,
  NTag,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import IconPicker from '@/components/icon/IconPicker.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

const { t } = useI18n()

defineOptions({ name: '菜单管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

// 表单初始化内容
const initForm = {
  order: 1,
  keepalive: true,
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '菜单',
  initForm,
  doCreate: api.createMenu,
  doDelete: api.deleteMenu,
  doUpdate: api.updateMenu,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
  getTreeSelect()
})

// 是否展示 "菜单类型"
const showMenuType = ref(false)
const menuOptions = ref([])

const columns = [
  { title: 'ID', key: 'id', width: 50, ellipsis: { tooltip: true }, align: 'center' },
  { title: t('views.system.menu.col_name'), key: 'name', width: 80, ellipsis: { tooltip: true }, align: 'center' },
  {
    title: t('views.system.menu.col_type'),
    key: 'menu_type',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      let round = false
      let bordered = false
      if (row.menu_type === 'catalog') {
        bordered = true
        round = false
      } else if (row.menu_type === 'menu') {
        bordered = false
        round = true
      }
      return h(
        NTag,
        { type: 'primary', round: round, bordered: bordered },
        { default: () => (row.menu_type === 'catalog' ? t('views.system.menu.type_catalog') : t('views.system.menu.type_menu')) }
      )
    },
  },
  {
    title: t('views.system.menu.col_icon'),
    key: 'icon',
    width: 40,
    align: 'center',
    render(row) {
      return h(TheIcon, { icon: row.icon, size: 20 })
    },
  },
  { title: t('views.system.menu.col_sort'), key: 'order', width: 40, ellipsis: { tooltip: true }, align: 'center' },
  { title: t('views.system.menu.col_path'), key: 'path', width: 80, ellipsis: { tooltip: true }, align: 'center' },
  { title: t('views.system.menu.col_redirect'), key: 'redirect', width: 80, ellipsis: { tooltip: true }, align: 'center' },
  { title: t('views.system.menu.col_component'), key: 'component', width: 80, ellipsis: { tooltip: true }, align: 'center' },
  {
    title: t('views.system.menu.col_keepalive'),
    key: 'keepalive',
    width: 40,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.keepalive,
        onUpdateValue: () => handleUpdateKeepalive(row),
      })
    },
  },
  {
    title: t('views.system.menu.col_hidden'),
    key: 'is_hidden',
    width: 40,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_hidden,
        onUpdateValue: () => handleUpdateHidden(row),
      })
    },
  },
  {
    title: t('views.system.menu.col_created'),
    key: 'created_at',
    width: 80,
    align: 'center',
    render(row) {
      return h('span', formatDate(row.created_at))
    },
  },
  {
    title: t('views.system.menu.col_actions'),
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
              style: `display: ${row.children && row.menu_type !== 'menu' ? '' : 'none'};`,
              onClick: () => {
                initForm.parent_id = row.id
                initForm.menu_type = 'menu'
                showMenuType.value = false
                handleAdd()
              },
            },
            [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'add'), t('views.system.menu.btn_new_child')]
          ),
          [[vPermission, 'post/api/v1/menu/create']]
        ),
        withDirectives(
          h(
            'button',
            {
              class: 'hm-row-btn',
              onClick: () => {
                showMenuType.value = false
                handleEdit(row)
              },
            },
            [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'edit'), t('views.system.menu.btn_edit')]
          ),
          [[vPermission, 'post/api/v1/menu/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }, false),
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  'button',
                  {
                    class: 'hm-row-btn danger',
                    style: `display: ${row.children && row.children.length > 0 ? 'none' : ''};`,
                  },
                  [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'delete'), t('views.system.menu.btn_delete')]
                ),
                [[vPermission, 'delete/api/v1/menu/delete']]
              ),
            default: () => h('div', {}, t('views.system.menu.confirm_delete')),
          }
        ),
      ]
    },
  },
]
// 修改是否keepalive
async function handleUpdateKeepalive(row) {
  if (!row.id) return
  row.publishing = true
  row.keepalive = row.keepalive === false ? true : false
  await api.updateMenu(row)
  row.publishing = false
  $message?.success(row.keepalive ? t('views.system.menu.msg_keepalive_on') : t('views.system.menu.msg_keepalive_off'))
}

// 修改是否隐藏
async function handleUpdateHidden(row) {
  if (!row.id) return
  row.publishing = true
  row.is_hidden = row.is_hidden === false ? true : false
  await api.updateMenu(row)
  row.publishing = false
  $message?.success(row.is_hidden ? t('views.system.menu.msg_hidden') : t('views.system.menu.msg_unhidden'))
}

// 新增菜单(可选目录)
function handleClickAdd() {
  initForm.parent_id = 0
  initForm.menu_type = 'catalog'
  initForm.is_hidden = false
  initForm.order = 1
  initForm.keepalive = true
  showMenuType.value = true
  handleAdd()
}

async function getTreeSelect() {
  const { data } = await api.getMenus()
  const menu = { id: 0, name: t('views.system.menu.root_dir'), children: [] }
  menu.children = data
  menuOptions.value = [menu]
}
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer :title="t('views.system.menu.page_title')">
    <template #action>
      <button class="hm-action-btn primary" v-permission="'post/api/v1/menu/create'" @click="handleClickAdd">
        <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
        {{ t('views.system.menu.btn_new_root') }}
      </button>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :is-pagination="false"
      :columns="columns"
      :get-data="api.getMenus"
      :single-line="true"
    >
    </CrudTable>

    <!-- 新增/编辑/查看 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave(getTreeSelect)"
    >
      <!-- 表单 -->
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
      >
        <NFormItem :label="t('views.system.menu.form_type')" path="menu_type">
          <NRadioGroup v-model:value="modalForm.menu_type">
            <NRadio :label="t('views.system.menu.type_catalog')" value="catalog" />
            <NRadio :label="t('views.system.menu.type_menu')" value="menu" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="t('views.system.menu.form_parent')" path="parent_id">
          <NTreeSelect
            v-model:value="modalForm.parent_id"
            key-field="id"
            label-field="name"
            :options="menuOptions"
            default-expand-all="true"
          />
        </NFormItem>
        <NFormItem
          :label="t('views.system.menu.form_name')"
          path="name"
          :rule="{
            required: true,
            message: t('views.system.menu.validate_name'),
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.name" :placeholder="t('views.system.menu.form_name_placeholder')" />
        </NFormItem>
        <NFormItem
          :label="t('views.system.menu.form_path')"
          path="path"
          :rule="{
            required: true,
            message: t('views.system.menu.validate_path'),
            trigger: ['blur'],
          }"
        >
          <NInput v-model:value="modalForm.path" :placeholder="t('views.system.menu.form_path_placeholder')" />
        </NFormItem>
        <NFormItem v-if="modalForm.menu_type === 'menu'" :label="t('views.system.menu.form_component')" path="component">
          <NInput
            v-model:value="modalForm.component"
            :placeholder="t('views.system.menu.form_component_placeholder')"
          />
        </NFormItem>
        <NFormItem :label="t('views.system.menu.form_redirect')" path="redirect">
          <NInput
            v-model:value="modalForm.redirect"
            :disabled="modalForm.parent_id !== 0"
            :placeholder="
              modalForm.parent_id !== 0 ? t('views.system.menu.form_redirect_hint') : t('views.system.menu.form_redirect_placeholder')
            "
          />
        </NFormItem>
        <NFormItem :label="t('views.system.menu.form_icon')" path="icon">
          <IconPicker v-model:value="modalForm.icon" />
        </NFormItem>
        <NFormItem :label="t('views.system.menu.form_sort')" path="order">
          <NInputNumber v-model:value="modalForm.order" :min="1" />
        </NFormItem>
        <NFormItem :label="t('views.system.menu.form_hidden')" path="is_hidden">
          <NSwitch v-model:value="modalForm.is_hidden" />
        </NFormItem>
        <NFormItem label="KeepAlive" path="keepalive">
          <NSwitch v-model:value="modalForm.keepalive" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
