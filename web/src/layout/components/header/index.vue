<template>
  <div flex items-center>
    <template v-if="isMobile">
      <button class="hm-mobile-menu-btn" @click="$emit('toggle-drawer')">
        <n-icon size="20">
          <icon-mdi:menu />
        </n-icon>
      </button>
    </template>
    <template v-else>
      <MenuCollapse />
      <BreadCrumb ml-15 hidden sm:block />
    </template>
  </div>
  <div ml-auto flex items-center>
    <Languages v-if="!isMobile" />
    <ThemeMode />
    <FullScreen v-if="!isMobile" />
    <UserAvatar />
  </div>
</template>

<script setup>
import BreadCrumb from './components/BreadCrumb.vue'
import MenuCollapse from './components/MenuCollapse.vue'
import FullScreen from './components/FullScreen.vue'
import UserAvatar from './components/UserAvatar.vue'
import ThemeMode from './components/ThemeMode.vue'
import Languages from './components/Languages.vue'

defineProps({
  isMobile: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle-drawer'])
</script>

<style scoped>
.hm-mobile-menu-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-primary);
  transition: all 0.25s var(--hm-spring);
}

.hm-mobile-menu-btn:active {
  background: var(--hm-pressed-bg, rgba(0, 0, 0, 0.06));
  transform: scale(0.92);
}
</style>
