<template>
  <AppPage :show-footer="showFooter">
    <header v-if="showHeader" mb-15 min-h-45 flex items-center justify-between px-15>
      <slot v-if="$slots.header" name="header" />
      <template v-else>
        <h1 class="head" dark:text-hex-ccc>{{ title || route.meta?.title }}</h1>
        <slot name="action" />
      </template>
    </header>
    <div class="content">
      <slot />
    </div>
  </AppPage>
</template>

<style scoped>
.head {
  font-size: 26px;
  font-weight: 700;
}
.content {
  padding: 0 15px;
}
</style>
<script setup>
defineProps({
  showFooter: {
    type: Boolean,
    default: false,
  },
  showHeader: {
    type: Boolean,
    default: true,
  },
  title: {
    type: String,
    default: undefined,
  },
})
const route = useRoute()
</script>
