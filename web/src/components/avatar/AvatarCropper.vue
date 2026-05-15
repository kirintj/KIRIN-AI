<template>
  <NModal v-model:show="visible" :mask-closable="false" preset="card" title="上传头像" style="width: 400px" :bordered="false">
    <div class="avatar-upload">
      <div class="preview-box">
        <img v-if="previewUrl" :src="previewUrl" class="preview-img" />
        <TheIcon v-else icon="material-symbols:add-a-photo" :size="48" color="#c0c4cc" />
      </div>
    </div>
    <template #footer>
      <div flex justify-end>
        <NButton @click="visible = false">取消</NButton>
        <NButton type="primary" ml-20 :loading="uploading" @click="handleConfirm">确认上传</NButton>
      </div>
    </template>
  </NModal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { NModal, NButton } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useFileUpload } from '@/composables/useFileUpload'

const props = defineProps({
  show: { type: Boolean, default: false },
  imgFile: { type: [File, null], default: null },
})
const emit = defineEmits(['update:show', 'uploaded'])

const visible = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v),
})
const { uploading, uploadAvatar } = useFileUpload()
const previewUrl = ref('')

watch(() => props.imgFile, (file) => {
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      previewUrl.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}, { immediate: true })

async function handleConfirm() {
  if (!props.imgFile) return
  const result = await uploadAvatar(props.imgFile)
  if (result) {
    emit('uploaded', result.avatar)
    visible.value = false
  }
}
</script>

<style scoped>
.avatar-upload {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}
.preview-box {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px dashed var(--hm-border);
  background: var(--hm-bg-container-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
