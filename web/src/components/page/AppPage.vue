<template>
  <transition name="fade-slide" mode="out-in" appear>
    <section class="cus-scroll-y wh-full flex-col p-l-15 p-r-15 dark:bg-hex-121212">
      <slot />
      <AppFooter v-if="showFooter" mt-15 />
      <n-back-top :bottom="20" />
    </section>
  </transition>
</template>

<script setup>
defineProps({
  showFooter: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
@media (max-width: 768px) {
  section {
    padding-left: 8px !important;
    padding-right: 8px !important;
  }
}
</style>
