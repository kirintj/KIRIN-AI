<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
  NTreeSelect,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import AvatarCropper from '@/components/avatar/AvatarCropper.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'

const { t } = useI18n()

defineOptions({ name: '用户管理' })

const roleNameMap = {
  '管理员': () => t('views.system.role.role_admin'),
  '普通用户': () => t('views.system.role.role_user'),
}

function getRoleName(name) {
  return roleNameMap[name] ? roleNameMap[name]() : name
}

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '用户',
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(),
})

const roleOption = ref([])
const deptOption = ref([])
const avatarFile = ref(null)
const cropperVisible = ref(false)
const avatarInputRef = ref(null)

const handleAvatarSelect = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    $message.warning(t('views.system.user.msg_select_image'))
    return
  }
  avatarFile.value = file
  cropperVisible.value = true
}

const handleAvatarUploaded = (avatarUrl) => {
  modalForm.value.avatar = avatarUrl
  cropperVisible.value = false
  avatarFile.value = null
}

const triggerAvatarSelect = () => {
  avatarInputRef.value?.click()
}

onMounted(() => {
  $table.value?.handleSearch()
  api.getRoleList({ page: 1, page_size: 9999 }).then((res) => (roleOption.value = res.data))
  api.getDepts().then((res) => (deptOption.value = res.data))
})

const columns = [
  {
    title: t('views.system.user.col_name'),
    key: 'username',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.user.col_email'),
    key: 'email',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.user.col_role'),
    key: 'role',
    width: 60,
    align: 'center',
    render(row) {
      const roles = row.roles ?? []
      const group = []
      for (let i = 0; i < roles.length; i++)
        group.push(
          h(NTag, { type: 'info', style: { margin: '2px 3px' } }, { default: () => getRoleName(roles[i].name) })
        )
      return h('span', group)
    },
  },
  {
    title: t('views.system.user.col_dept'),
    key: 'dept.name',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.user.col_superuser'),
    key: 'is_superuser',
    align: 'center',
    width: 40,
    render(row) {
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => (row.is_superuser ? t('views.system.user.value_yes') : t('views.system.user.value_no')) }
      )
    },
  },
  {
    title: t('views.system.user.col_last_login'),
    key: 'last_login',
    align: 'center',
    width: 80,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.last_login !== null ? formatDate(row.last_login) : null),
          icon: renderIcon('mdi:update', { size: 16 }),
        }
      )
    },
  },
  {
    title: t('views.system.user.col_disabled'),
    key: 'is_active',
    width: 50,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_active,
        loading: !!row.publishing,
        checkedValue: false,
        uncheckedValue: true,
        onUpdateValue: () => handleUpdateDisable(row),
      })
    },
  },
  {
    title: t('views.system.user.col_actions'),
    key: 'actions',
    width: 220,
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
                modalForm.value.dept_id = row.dept?.id
                modalForm.value.role_ids = row.roles.map((e) => (e = e.id))
                delete modalForm.value.dept
              },
            },
            t('views.system.user.btn_edit')
          ),
          [[vPermission, 'post/api/v1/user/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ user_id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  'button',
                  { class: 'hm-row-btn danger' },
                  t('views.system.user.btn_delete')
                ),
                [[vPermission, 'delete/api/v1/user/delete']]
              ),
            default: () => h('div', {}, t('views.system.user.confirm_delete')),
          }
        ),
        !row.is_superuser && h(
          NPopconfirm,
          {
            onPositiveClick: async () => {
              try {
                await api.resetPassword({ user_id: row.id });
                $message.success(t('views.system.user.msg_reset_success'));
                await $table.value?.handleSearch();
              } catch (error) {
                $message.error(t('views.system.user.msg_reset_failed', { error: error.message }));
              }
            },
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  'button',
                  { class: 'hm-row-btn' },
                  t('views.system.user.btn_reset_password')
                ),
                [[vPermission, 'post/api/v1/user/reset_password']]
              ),
            default: () => h('div', {}, t('views.system.user.confirm_reset')),
          }
        ),
      ]
    },
  },
]

// 修改用户禁用状态
async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) {
    $message.error(t('views.system.user.msg_cannot_disable_self'))
    return
  }
  row.publishing = true
  row.is_active = row.is_active === false ? true : false
  row.publishing = false
  const role_ids = []
  row.roles.forEach((e) => {
    role_ids.push(e.id)
  })
  row.role_ids = role_ids
  row.dept_id = row.dept?.id
  try {
    await api.updateUser(row)
    $message?.success(row.is_active ? t('views.system.user.msg_enabled') : t('views.system.user.msg_disabled'))
    $table.value?.handleSearch()
  } catch (err) {
    // 有异常恢复原来的状态
    row.is_active = row.is_active === false ? true : false
  } finally {
    row.publishing = false
  }
}

let lastClickedNodeId = null

const nodeProps = ({ option }) => {
  return {
    onClick() {
      if (lastClickedNodeId === option.id) {
        $table.value?.handleSearch()
        lastClickedNodeId = null
      } else {
        api.getUserList({ dept_id: option.id }).then((res) => {
          $table.value.tableData = res.data
          lastClickedNodeId = option.id
        })
      }
    },
  }
}

const validateAddUser = {
  username: [
    {
      required: true,
      message: t('views.system.user.validate_name'),
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: t('views.system.user.validate_email'),
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        const re = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
        if (!re.test(modalForm.value.email)) {
          callback(t('views.system.user.validate_email_format'))
          return
        }
        callback()
      },
    },
  ],
  password: [
    {
      required: true,
      message: t('views.system.user.validate_password'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: t('views.system.user.validate_confirm'),
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) {
          callback(t('views.system.user.validate_password_diff'))
          return
        }
        callback()
      },
    },
  ],
  roles: [
    {
      type: 'array',
      required: true,
      message: t('views.system.user.validate_role'),
      trigger: ['blur', 'change'],
    },
  ],
}
</script>

<template>
  <div class="hm-user-layout">
  <div class="hm-sidebar">
    <div class="hm-sidebar-header">
      <span class="hm-sidebar-title">{{ t('views.system.user.sidebar_title') }}</span>
    </div>
    <div class="hm-dept-tree-wrap">
      <NTree
        block-line
        :data="deptOption"
        key-field="id"
        label-field="name"
        default-expand-all
        :node-props="nodeProps"
      />
    </div>
  </div>
  <div class="hm-user-main">
      <CommonPage show-footer :title="t('views.system.user.page_title')">
        <template #action>
          <button class="hm-action-btn primary" v-permission="'post/api/v1/user/create'" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
            {{ t('views.system.user.btn_new') }}
          </button>
        </template>
        <!-- 表格 -->
        <CrudTable
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="api.getUserList"
        >
          <template #queryBar>
            <QueryBarItem :label="t('views.system.user.search_name')" :label-width="40">
              <NInput
                v-model:value="queryItems.username"
                clearable
                type="text"
                :placeholder="t('views.system.user.search_name_placeholder')"
                @keypress.enter="$table?.handleSearch()"
              />
            </QueryBarItem>
            <QueryBarItem :label="t('views.system.user.search_email')" :label-width="40">
              <NInput
                v-model:value="queryItems.email"
                clearable
                type="text"
                :placeholder="t('views.system.user.search_email_placeholder')"
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
            :rules="validateAddUser"
          >
            <NFormItem label="头像" path="avatar">
              <div class="avatar-form-item">
                <div class="avatar-preview-box" @click="triggerAvatarSelect">
                  <img v-if="modalForm.avatar" :src="modalForm.avatar" class="avatar-preview-img" />
                  <TheIcon v-else icon="material-symbols:add-a-photo" :size="32" color="#c0c4cc" />
                </div>
                <input
                  ref="avatarInputRef"
                  type="file"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  style="display: none"
                  @change="handleAvatarSelect"
                />
                <span class="avatar-tip">{{ t('views.system.user.avatar_tip') }}</span>
              </div>
            </NFormItem>
            <NFormItem :label="t('views.system.user.form_name')" path="username">
              <NInput v-model:value="modalForm.username" clearable :placeholder="t('views.system.user.form_name_placeholder')" />
            </NFormItem>
            <NFormItem :label="t('views.system.user.form_email')" path="email">
              <NInput v-model:value="modalForm.email" clearable :placeholder="t('views.system.user.form_email_placeholder')" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" :label="t('views.system.user.form_password')" path="password">
              <NInput
                v-model:value="modalForm.password"
                show-password-on="mousedown"
                type="password"
                clearable
                :placeholder="t('views.system.user.form_password_placeholder')"
              />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" :label="t('views.system.user.form_confirm')" path="confirmPassword">
              <NInput
                v-model:value="modalForm.confirmPassword"
                show-password-on="mousedown"
                type="password"
                clearable
                :placeholder="t('views.system.user.form_confirm_placeholder')"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.user.form_role')" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox
                    v-for="item in roleOption"
                    :key="item.id"
                    :value="item.id"
                    :label="getRoleName(item.name)"
                  />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>
            <NFormItem :label="t('views.system.user.form_superuser')" path="is_superuser">
              <NSwitch
                v-model:value="modalForm.is_superuser"
                size="small"
                :checked-value="true"
                :unchecked-value="false"
              ></NSwitch>
            </NFormItem>
            <NFormItem :label="t('views.system.user.form_disabled')" path="is_active">
              <NSwitch
                v-model:value="modalForm.is_active"
                :checked-value="false"
                :unchecked-value="true"
                :default-value="true"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.user.form_dept')" path="dept_id">
              <NTreeSelect
                v-model:value="modalForm.dept_id"
                :options="deptOption"
                key-field="id"
                label-field="name"
                :placeholder="t('views.system.user.form_dept_placeholder')"
                clearable
                default-expand-all
              ></NTreeSelect>
            </NFormItem>
          </NForm>
        </CrudModal>
      </CommonPage>
  </div>
  <!-- 头像裁剪弹窗 -->
  <AvatarCropper
    v-model:show="cropperVisible"
    :img-file="avatarFile"
    @uploaded="handleAvatarUploaded"
  />
  </div>
</template>

<style scoped>
.hm-user-layout {
  height: 100%;
  display: flex;
  background: var(--hm-bg-primary);
  overflow: hidden;
}

.hm-user-main {
  flex: 1;
  overflow: auto;
  min-width: 0;
}

.hm-dept-tree-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}

.avatar-form-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar-preview-box {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 2px dashed var(--hm-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
  flex-shrink: 0;
}
.avatar-preview-box:hover {
  border-color: var(--hm-brand);
}
.avatar-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-tip {
  font-size: 12px;
  color: var(--hm-font-fourth);
}
</style>
