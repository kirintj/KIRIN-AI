<template>
  <div v-if="reloadFlag" class="relative">
    <slot></slot>
    <div v-show="showPlaceholder" class="absolute-lt h-full w-full" :class="placeholderClass">
      <div v-show="loading" class="absolute-center">
        <n-spin :show="true" :size="loadingSize" />
      </div>
      <div v-show="isEmpty" class="absolute-center">
        <div class="relative">
          <icon-custom-no-data :class="iconClass" />
          <p class="absolute-lb w-full text-center" :class="descClass">{{ emptyDesc }}</p>
        </div>
      </div>
      <div v-show="!network" class="absolute-center">
        <div
          class="relative"
          :class="{ 'cursor-pointer': showNetworkReload }"
          @click="handleReload"
        >
          <icon-custom-network-error :class="iconClass" />
          <p class="absolute-lb w-full text-center" :class="descClass">{{ networkErrorDesc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onUnmounted } from 'vue'

defineOptions({ name: 'LoadingEmptyWrapper' })

const NETWORK_ERROR_MSG = '网络似乎开了小差~'

const props = defineProps({
  loading: { type: Boolean, default: false },
  empty: { type: Boolean, default: false },
  loadingSize: { type: String, default: 'medium' },
  placeholderClass: {
    type: String,
    default: 'bg-white dark:bg-dark transition-background-color duration-300 ease-in-out',
  },
  emptyDesc: { type: String, default: '暂无数据' },
  iconClass: { type: String, default: 'text-320px text-primary' },
  descClass: { type: String, default: 'text-16px text-#666' },
  showNetworkReload: { type: Boolean, default: false },
})

// 网络状态
const network = ref(window.navigator.onLine)
const reloadFlag = ref(true)

// 数据是否为空
const isEmpty = computed(() => props.empty && !props.loading && network.value)

const showPlaceholder = computed(() => props.loading || isEmpty.value || !network.value)

const networkErrorDesc = computed(() =>
  props.showNetworkReload ? `${NETWORK_ERROR_MSG}, 点击重试` : NETWORK_ERROR_MSG
)

function handleReload() {
  if (!props.showNetworkReload) return
  reloadFlag.value = false
  nextTick(() => {
    reloadFlag.value = true
  })
}

const stopHandle = watch(
  () => props.loading,
  (newValue) => {
    // 结束加载判断一下网络状态
    if (!newValue) {
      network.value = window.navigator.onLine
    }
  }
)

onUnmounted(() => {
  stopHandle()
})
</script>

<style scoped></style>
