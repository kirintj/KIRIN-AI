<template>
  <n-dropdown :options="options" @select="handleSelect">
    <div flex cursor-pointer items-center>
      <img :src="userStore.avatar" mr10 h-35 w-35 rounded-full />
      <span v-if="!isMobile" class="hm-user-name">{{ userStore.name }}</span>
    </div>
  </n-dropdown>
</template>

<script setup>
import { useUserStore } from '@/store'
import { renderIcon } from '@/utils'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useBreakpoints } from '@vueuse/core'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const breakpoints = reactive(useBreakpoints({ sm: 666 }))
const isMobile = breakpoints.smaller('sm')

const options = [
  {
    label: t('header.label_profile'),
    key: 'profile',
    icon: renderIcon('mdi-account-arrow-right-outline', { size: '14px' }),
  },
  {
    label: t('header.label_logout'),
    key: 'logout',
    icon: renderIcon('mdi:exit-to-app', { size: '14px' }),
  },
]

function handleSelect(key) {
  if (key === 'profile') {
    router.push('/profile')
  } else if (key === 'logout') {
    $dialog.confirm({
      title: t('header.label_logout_dialog_title'),
      type: 'warning',
      content: t('header.text_logout_confirm'),
      confirm() {
        userStore.logout()
        $message.success(t('header.text_logout_success'))
      },
    })
  }
}
</script>

<style scoped>
@media (max-width: 768px) {
  .hm-user-name {
    display: none;
  }
}
</style>
