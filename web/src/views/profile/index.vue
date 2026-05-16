<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import CommonPage from '@/components/page/CommonPage.vue'
import AvatarCropper from '@/components/avatar/AvatarCropper.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'
import api from '@/api'

const { t } = useI18n()
const userStore = useUserStore()
const isLoading = ref(false)
const activeTab = ref('info')

const infoFormRef = ref(null)
const infoForm = ref({
  avatar: userStore.avatar,
  username: userStore.name,
  email: userStore.email,
})

watch(
  () => [userStore.avatar, userStore.name, userStore.email],
  ([avatar, username, email]) => {
    infoForm.value = { avatar, username, email }
  },
)

const avatarFile = ref(null)
const cropperVisible = ref(false)
const avatarInputRef = ref(null)

const handleAvatarSelect = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    $message.warning(t('views.profile.message_select_image'))
    return
  }
  avatarFile.value = file
  cropperVisible.value = true
}

const handleAvatarUploaded = (avatarUrl) => {
  infoForm.value.avatar = avatarUrl
  cropperVisible.value = false
  avatarFile.value = null
}

const triggerAvatarSelect = () => {
  avatarInputRef.value?.click()
}

async function updateProfile() {
  infoFormRef.value?.validate(async (err) => {
    if (err) return
    isLoading.value = true
    await api
      .updateUser({ ...infoForm.value, id: userStore.userId })
      .then(() => {
        userStore.setUserInfo(infoForm.value)
        $message.success(t('common.messages.update_success'))
      })
      .catch(() => {})
      .finally(() => {
        isLoading.value = false
      })
  })
}
const infoFormRules = {
  username: [
    {
      required: true,
      message: t('views.profile.message_username_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

const passwordFormRef = ref(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

async function updatePassword() {
  passwordFormRef.value?.validate(async (err) => {
    if (err) return
    isLoading.value = true
    const data = { ...passwordForm.value, id: userStore.userId }
    await api
      .updatePassword(data)
      .then((res) => {
        $message.success(res.msg)
        passwordForm.value = {
          old_password: '',
          new_password: '',
          confirm_password: '',
        }
      })
      .catch(() => {})
      .finally(() => {
        isLoading.value = false
      })
  })
}
const passwordFormRules = {
  old_password: [
    {
      required: true,
      message: t('views.profile.message_old_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  new_password: [
    {
      required: true,
      message: t('views.profile.message_new_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirm_password: [
    {
      required: true,
      message: t('views.profile.message_password_confirmation_required'),
      trigger: ['input', 'blur'],
    },
    {
      validator: validatePasswordStartWith,
      message: t('views.profile.message_password_confirmation_diff'),
      trigger: 'input',
    },
    {
      validator: validatePasswordSame,
      message: t('views.profile.message_password_confirmation_diff'),
      trigger: ['blur', 'password-input'],
    },
  ],
}
function validatePasswordStartWith(rule, value) {
  return (
    !!passwordForm.value.new_password &&
    passwordForm.value.new_password.startsWith(value) &&
    passwordForm.value.new_password.length >= value.length
  )
}
function validatePasswordSame(rule, value) {
  return value === passwordForm.value.new_password
}
</script>

<template>
  <CommonPage :show-header="false">
    <div class="hm-profile">
      <div class="hm-profile-header">
        <h1 class="hm-profile-title">{{ $t('views.profile.label_modify_information') }}</h1>
        <p class="hm-profile-subtitle">{{ t('views.profile.subtitle') }}</p>
      </div>

      <div class="hm-profile-tabs">
        <button
          class="hm-tab-btn"
          :class="{ active: activeTab === 'info' }"
          @click="activeTab = 'info'"
        >
          <TheIcon icon="icon-park-outline:user" :size="16" />
          {{ $t('views.profile.label_modify_information') }}
        </button>
        <button
          class="hm-tab-btn"
          :class="{ active: activeTab === 'password' }"
          @click="activeTab = 'password'"
        >
          <TheIcon icon="icon-park-outline:lock" :size="16" />
          {{ $t('views.profile.label_change_password') }}
        </button>
      </div>

      <!-- Info Card -->
      <div v-show="activeTab === 'info'" class="hm-profile-card">
        <NForm
          ref="infoFormRef"
          label-placement="left"
          label-align="left"
          label-width="100"
          :model="infoForm"
          :rules="infoFormRules"
        >
          <NFormItem :label="$t('views.profile.label_avatar')" path="avatar">
            <div class="hm-avatar-section">
              <div class="hm-avatar-box" @click="triggerAvatarSelect">
                <img v-if="infoForm.avatar" :src="infoForm.avatar" class="hm-avatar-img" />
                <TheIcon v-else icon="material-symbols:add-a-photo" :size="32" color="var(--hm-font-tertiary)" />
              </div>
              <div class="hm-avatar-meta">
                <span class="hm-avatar-name">{{ infoForm.username }}</span>
                <span class="hm-avatar-tip">{{ t('views.profile.avatar_tip') }}</span>
              </div>
              <input
                ref="avatarInputRef"
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                style="display: none"
                @change="handleAvatarSelect"
              />
            </div>
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_username')" path="username">
            <NInput
              v-model:value="infoForm.username"
              type="text"
              :placeholder="$t('views.profile.placeholder_username')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_email')" path="email">
            <NInput
              v-model:value="infoForm.email"
              type="text"
              :placeholder="$t('views.profile.placeholder_email')"
            />
          </NFormItem>
          <div class="hm-form-actions">
            <NButton type="primary" :loading="isLoading" @click="updateProfile">
              {{ $t('common.actions.save') }}
            </NButton>
          </div>
        </NForm>
      </div>

      <!-- Password Card -->
      <div v-show="activeTab === 'password'" class="hm-profile-card">
        <NForm
          ref="passwordFormRef"
          label-placement="left"
          label-align="left"
          label-width="120"
          :model="passwordForm"
          :rules="passwordFormRules"
        >
          <NFormItem :label="$t('views.profile.label_old_password')" path="old_password">
            <NInput
              v-model:value="passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_old_password')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_new_password')" path="new_password">
            <NInput
              v-model:value="passwordForm.new_password"
              :disabled="!passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_new_password')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_confirm_password')" path="confirm_password">
            <NInput
              v-model:value="passwordForm.confirm_password"
              :disabled="!passwordForm.new_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_confirm_password')"
            />
          </NFormItem>
          <div class="hm-form-actions">
            <NButton type="primary" :loading="isLoading" @click="updatePassword">
              {{ $t('common.actions.save') }}
            </NButton>
          </div>
        </NForm>
      </div>
    </div>

    <AvatarCropper
      v-model:show="cropperVisible"
      :img-file="avatarFile"
      @uploaded="handleAvatarUploaded"
    />
  </CommonPage>
</template>

<style scoped>
.hm-profile {
  max-width: 640px;
  margin: 0 auto;
  padding: 32px 16px;
}

.hm-profile-header {
  margin-bottom: 28px;
}

.hm-profile-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
}

.hm-profile-subtitle {
  font-size: 14px;
  color: var(--hm-font-tertiary);
}

.hm-profile-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: var(--hm-bg-glass);
  backdrop-filter: blur(8px);
  border-radius: var(--hm-radius-lg, 12px);
  padding: 4px;
  border: 1px solid var(--hm-border-glass);
}

.hm-tab-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--hm-radius-md, 8px);
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-secondary);
  cursor: pointer;
  transition: all 0.3s var(--hm-spring);
}

.hm-tab-btn:hover {
  color: var(--hm-font-primary);
  background: var(--hm-brand-bg-light);
}

.hm-tab-btn.active {
  color: var(--hm-brand);
  background: var(--hm-bg-glass);
  box-shadow: 0 2px 8px rgba(10, 89, 247, 0.1);
}

.hm-profile-card {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass-strong, blur(12px));
  -webkit-backdrop-filter: var(--hm-blur-glass-strong, blur(12px));
  border-radius: var(--hm-radius-xl, 16px);
  border: 1px solid var(--hm-border-glass);
  padding: 32px;
  box-shadow: var(--hm-shadow-layered, 0 4px 24px rgba(0, 0, 0, 0.06));
}

.hm-avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hm-avatar-box {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px dashed var(--hm-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s var(--hm-spring);
  flex-shrink: 0;
  background: var(--hm-bg-glass);
  backdrop-filter: blur(8px);
}

.hm-avatar-box:hover {
  border-color: var(--hm-brand);
  box-shadow: 0 0 0 3px var(--hm-focus-ring);
  transform: scale(1.05);
}

.hm-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hm-avatar-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-avatar-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-avatar-tip {
  font-size: 12px;
  color: var(--hm-font-tertiary);
}

.hm-form-actions {
  padding-top: 8px;
}

@media (max-width: 480px) {
  .hm-profile {
    padding: 16px 8px;
  }

  .hm-profile-card {
    padding: 20px 16px;
  }

  .hm-profile-title {
    font-size: 20px;
  }

  .hm-avatar-box {
    width: 56px;
    height: 56px;
  }
}
</style>
