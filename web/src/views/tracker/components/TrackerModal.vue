<script lang="ts">
import { computed } from 'vue'
import { NModal, NForm, NFormItem, NInput, NSelect } from 'naive-ui'

export default {
  inheritAttrs: false,
}
</script>

<script setup lang="ts">
const props = defineProps<{
  show: boolean
  mode: 'add' | 'edit'
  formData: any
  statusOptions: { label: string; value: string }[]
  sourceOptions: { label: string; value: string }[]
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: []
}>()

const title = computed(() => props.mode === 'add' ? '添加求职记录' : '编辑求职记录')
const confirmText = computed(() => props.mode === 'add' ? '添加' : '保存')
</script>

<template>
  <NModal :show="show" preset="card" :title="title" style="width: 480px" @update:show="emit('update:show', $event)">
    <NForm v-if="formData" label-placement="left" label-width="60">
      <NFormItem label="公司">
        <NInput v-model:value="formData.company" placeholder="公司名称" />
      </NFormItem>
      <NFormItem label="职位">
        <NInput v-model:value="formData.position" placeholder="职位名称" />
      </NFormItem>
      <NFormItem label="状态">
        <NSelect v-model:value="formData.status" :options="statusOptions" />
      </NFormItem>
      <NFormItem label="薪资">
        <NInput v-model:value="formData.salary" placeholder="如 20-30K" />
      </NFormItem>
      <NFormItem label="地点">
        <NInput v-model:value="formData.location" placeholder="如 北京" />
      </NFormItem>
      <NFormItem label="渠道">
        <NSelect
          v-if="mode === 'add'"
          v-model:value="formData.source"
          :options="sourceOptions"
          clearable
          placeholder="投递渠道"
        />
        <NInput v-else v-model:value="formData.source" />
      </NFormItem>
      <NFormItem label="备注">
        <NInput v-model:value="formData.notes" type="textarea" :rows="2" placeholder="备注信息" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="hm-modal-footer">
        <button class="hm-modal-btn" @click="emit('update:show', false)">取消</button>
        <button class="hm-modal-btn primary" @click="emit('submit')">{{ confirmText }}</button>
      </div>
    </template>
  </NModal>
</template>
