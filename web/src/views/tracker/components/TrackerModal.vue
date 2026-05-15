<script lang="ts">
import { computed } from 'vue'
import { NModal, NForm, NFormItem, NInput, NSelect } from 'naive-ui'

export default {
  inheritAttrs: false,
}
</script>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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

const title = computed(() => props.mode === 'add' ? t('views.tracker.modal_add_title') : t('views.tracker.modal_edit_title'))
const confirmText = computed(() => props.mode === 'add' ? t('views.tracker.btn_add') : t('views.tracker.btn_save'))
</script>

<template>
  <NModal :show="show" preset="card" :title="title" style="width: 480px" @update:show="emit('update:show', $event)">
    <NForm v-if="formData" label-placement="left" label-width="60">
      <NFormItem :label="t('views.tracker.form_company')">
        <NInput v-model:value="formData.company" :placeholder="t('views.tracker.form_company_placeholder')" />
      </NFormItem>
      <NFormItem :label="t('views.tracker.form_position')">
        <NInput v-model:value="formData.position" :placeholder="t('views.tracker.form_position_placeholder')" />
      </NFormItem>
      <NFormItem :label="t('views.tracker.form_status')">
        <NSelect v-model:value="formData.status" :options="statusOptions" />
      </NFormItem>
      <NFormItem :label="t('views.tracker.form_salary')">
        <NInput v-model:value="formData.salary" :placeholder="t('views.tracker.form_salary_placeholder')" />
      </NFormItem>
      <NFormItem :label="t('views.tracker.form_location')">
        <NInput v-model:value="formData.location" :placeholder="t('views.tracker.form_location_placeholder')" />
      </NFormItem>
      <NFormItem :label="t('views.tracker.form_source')">
        <NSelect
          v-if="mode === 'add'"
          v-model:value="formData.source"
          :options="sourceOptions"
          clearable
          :placeholder="t('views.tracker.form_source_placeholder')"
        />
        <NInput v-else v-model:value="formData.source" />
      </NFormItem>
      <NFormItem :label="t('views.tracker.form_notes')">
        <NInput v-model:value="formData.notes" type="textarea" :rows="2" :placeholder="t('views.tracker.form_notes_placeholder')" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="hm-modal-footer">
        <button class="hm-modal-btn" @click="emit('update:show', false)">{{ t('common.actions.cancel') }}</button>
        <button class="hm-modal-btn primary" @click="emit('submit')">{{ confirmText }}</button>
      </div>
    </template>
  </NModal>
</template>
