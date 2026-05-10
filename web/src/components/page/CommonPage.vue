<template>
  <AppPage :show-footer="showFooter">
    <div class="hm-page-wrap">
      <header v-if="showHeader" class="hm-page-header">
        <slot v-if="$slots.header" name="header" />
        <template v-else>
          <div>
            <h1 class="hm-page-title">{{ title || route.meta?.title }}</h1>
          </div>
          <slot name="action" />
        </template>
      </header>
      <div class="hm-page-content">
        <slot />
      </div>
    </div>
  </AppPage>
</template>

<style scoped>
.hm-page-wrap {
  width: 100%;
  margin: 0 auto;
  padding: 32px 28px;
}

.hm-page-content {
  min-height: 0;
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
