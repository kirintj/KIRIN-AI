<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
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

defineOptions({ name: '用户管理' })

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
    $message.warning('请选择图片文件')
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
    title: '名称',
    key: 'username',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '邮箱',
    key: 'email',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '用户角色',
    key: 'role',
    width: 60,
    align: 'center',
    render(row) {
      const roles = row.roles ?? []
      const group = []
      for (let i = 0; i < roles.length; i++)
        group.push(
          h(NTag, { type: 'info', style: { margin: '2px 3px' } }, { default: () => roles[i].name })
        )
      return h('span', group)
    },
  },
  {
    title: '部门',
    key: 'dept.name',
    align: 'center',
    width: 40,
    ellipsis: { tooltip: true },
  },
  {
    title: '超级用户',
    key: 'is_superuser',
    align: 'center',
    width: 40,
    render(row) {
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => (row.is_superuser ? '是' : '否') }
      )
    },
  },
  {
    title: '上次登录时间',
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
    title: '禁用',
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
    title: '操作',
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
            [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'edit'), '编辑']
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
                  [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'delete'), '删除']
                ),
                [[vPermission, 'delete/api/v1/user/delete']]
              ),
            default: () => h('div', {}, '确定删除该用户吗?'),
          }
        ),
        !row.is_superuser && h(
          NPopconfirm,
          {
            onPositiveClick: async () => {
              try {
                await api.resetPassword({ user_id: row.id });
                $message.success('密码已成功重置为123456');
                await $table.value?.handleSearch();
              } catch (error) {
                $message.error('重置密码失败: ' + error.message);
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
                  [h('i', { class: 'material-symbols', style: 'font-size:14px' }, 'lock'), '重置密码']
                ),
                [[vPermission, 'post/api/v1/user/reset_password']]
              ),
            default: () => h('div', {}, '确定重置用户密码为123456吗?'),
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
    $message.error('当前登录用户不可禁用！')
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
    $message?.success(row.is_active ? '已取消禁用该用户' : '已禁用该用户')
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
      message: '请输入名称',
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: '请输入邮箱地址',
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        const re = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
        if (!re.test(modalForm.value.email)) {
          callback('邮箱格式错误')
          return
        }
        callback()
      },
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) {
          callback('两次密码输入不一致')
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
      message: '请至少选择一个角色',
      trigger: ['blur', 'change'],
    },
  ],
}
</script>

<template>
  <div class="hm-user-layout">
  <div class="hm-sidebar">
    <div class="hm-sidebar-header">
      <span class="hm-sidebar-title">部门列表</span>
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
      <CommonPage show-footer title="用户列表">
        <template #action>
          <button class="hm-action-btn primary" v-permission="'post/api/v1/user/create'" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="16" color="#fff" />
            新建用户
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
            <QueryBarItem label="名称" :label-width="40">
              <NInput
                v-model:value="queryItems.username"
                clearable
                type="text"
                placeholder="请输入用户名称"
                @keypress.enter="$table?.handleSearch()"
              />
            </QueryBarItem>
            <QueryBarItem label="邮箱" :label-width="40">
              <NInput
                v-model:value="queryItems.email"
                clearable
                type="text"
                placeholder="请输入邮箱"
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
                <span class="avatar-tip">点击上传头像，将自动裁剪为正方形</span>
              </div>
            </NFormItem>
            <NFormItem label="用户名称" path="username">
              <NInput v-model:value="modalForm.username" clearable placeholder="请输入用户名称" />
            </NFormItem>
            <NFormItem label="邮箱" path="email">
              <NInput v-model:value="modalForm.email" clearable placeholder="请输入邮箱" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="密码" path="password">
              <NInput
                v-model:value="modalForm.password"
                show-password-on="mousedown"
                type="password"
                clearable
                placeholder="请输入密码"
              />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
              <NInput
                v-model:value="modalForm.confirmPassword"
                show-password-on="mousedown"
                type="password"
                clearable
                placeholder="请确认密码"
              />
            </NFormItem>
            <NFormItem label="角色" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox
                    v-for="item in roleOption"
                    :key="item.id"
                    :value="item.id"
                    :label="item.name"
                  />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>
            <NFormItem label="超级用户" path="is_superuser">
              <NSwitch
                v-model:value="modalForm.is_superuser"
                size="small"
                :checked-value="true"
                :unchecked-value="false"
              ></NSwitch>
            </NFormItem>
            <NFormItem label="禁用" path="is_active">
              <NSwitch
                v-model:value="modalForm.is_active"
                :checked-value="false"
                :unchecked-value="true"
                :default-value="true"
              />
            </NFormItem>
            <NFormItem label="部门" path="dept_id">
              <NTreeSelect
                v-model:value="modalForm.dept_id"
                :options="deptOption"
                key-field="id"
                label-field="name"
                placeholder="请选择部门"
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
  border: 2px dashed #dcdfe6;
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
