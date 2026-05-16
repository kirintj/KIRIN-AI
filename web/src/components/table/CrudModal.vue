<template>
  <n-modal
    v-model:show="show"
    :style="{ width }"
    preset="card"
    :title="title"
    size="huge"
    :bordered="false"
    :mask-closable="false"
  >
    <slot />
    <template v-if="showFooter" #footer>
      <footer class="hm-modal-footer">
        <slot name="footer">
          <button class="hm-modal-btn" @click="show = false">{{ t('common.actions.cancel') }}</button>
          <button class="hm-modal-btn primary" :disabled="loading" @click="emit('save')">
            <span v-if="loading" class="hm-modal-loading"></span>
            {{ t('common.actions.save') }}
          </button>
        </slot>
      </footer>
    </template>
  </n-modal>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  width: {
    type: String,
    default: '600px',
  },
  title: {
    type: String,
    default: '',
  },
  showFooter: {
    type: Boolean,
    default: true,
  },
  visible: {
    type: Boolean,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:visible', 'onSave'])
const show = computed({
  get() {
    return props.visible
  },
  set(v) {
    emit('update:visible', v)
  },
})
</script>

<style scoped>
.hm-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.hm-modal-btn {
  padding: 7px 18px;
  border: 1px solid var(--hm-border);
  border-radius: var(--hm-radius-full);
  background: var(--hm-bg-secondary);
  font-size: 13px;
  color: var(--hm-font-primary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-modal-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  transform: translateY(-1px);
  box-shadow: var(--hm-glow-brand);
}

.hm-modal-btn.primary {
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: var(--hm-glow-brand);
}

.hm-modal-btn.primary:hover {
  box-shadow: var(--hm-glow-brand-strong);
  transform: translateY(-1px);
}

.hm-modal-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.hm-modal-loading {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: hm-spin 0.6s linear infinite;
  margin-right: 4px;
  vertical-align: middle;
}

@keyframes hm-spin {
  to { transform: rotate(360deg); }
}
</style>
