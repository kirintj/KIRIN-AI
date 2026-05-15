<template>
  <div class="slider-captcha">
    <div class="slider-captcha__bg" ref="bgRef">
      <img :src="'data:image/png;base64,' + bg" alt="captcha" draggable="false" />
      <img
        class="slider-captcha__piece"
        :src="'data:image/png;base64,' + slider"
        :style="{ top: y + 'px', left: sliderLeft + 'px' }"
        alt="slider"
        draggable="false"
      />
    </div>
    <div class="slider-captcha__track">
      <div class="slider-captcha__track-fill" :style="{ width: sliderLeft + 'px' }"></div>
      <div
        class="slider-captcha__thumb"
        :style="{ left: sliderLeft + 'px' }"
        @mousedown="onStart"
        @touchstart.prevent="onStart"
      >
        <span v-if="!dragging && !verified">→</span>
        <span v-else-if="verified">✓</span>
      </div>
      <div class="slider-captcha__text">{{ verified ? '验证成功' : '向右滑动完成验证' }}</div>
    </div>
    <div class="slider-captcha__refresh" @click="$emit('refresh')">↻</div>
  </div>
</template>

<script setup>
const props = defineProps({
  bg: { type: String, required: true },
  slider: { type: String, required: true },
  y: { type: Number, default: 0 },
})

const emit = defineEmits(['success', 'fail', 'refresh'])

const bgRef = ref(null)
const sliderLeft = ref(0)
const dragging = ref(false)
const verified = ref(false)
const startX = ref(0)

function onStart(e) {
  if (verified.value) return
  dragging.value = true
  startX.value = (e.touches ? e.touches[0] : e).clientX - sliderLeft.value

  const onMove = (ev) => {
    if (!dragging.value) return
    const clientX = (ev.touches ? ev.touches[0] : ev).clientX
    const bgWidth = bgRef.value?.offsetWidth || 280
    let left = clientX - startX.value
    left = Math.max(0, Math.min(left, bgWidth - 40))
    sliderLeft.value = left
  }

  const onEnd = () => {
    dragging.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onEnd)
    document.removeEventListener('touchmove', onMove)
    document.removeEventListener('touchend', onEnd)

    const bgWidth = bgRef.value?.offsetWidth || 280
    if (sliderLeft.value > bgWidth - 60) {
      verified.value = true
      emit('success', { x: Math.round(sliderLeft.value) })
    } else {
      sliderLeft.value = 0
      emit('fail')
    }
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onEnd)
  document.addEventListener('touchmove', onMove, { passive: false })
  document.addEventListener('touchend', onEnd)
}

function reset() {
  sliderLeft.value = 0
  verified.value = false
  dragging.value = false
}

defineExpose({ reset })
</script>

<style scoped>
.slider-captcha {
  width: 100%;
  user-select: none;
}

.slider-captcha__bg {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.slider-captcha__bg img {
  width: 100%;
  display: block;
}

.slider-captcha__piece {
  position: absolute;
  pointer-events: none;
}

.slider-captcha__track {
  position: relative;
  width: 100%;
  height: 40px;
  background: #e8e8e8;
  border-radius: 20px;
  overflow: hidden;
}

.slider-captcha__track-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #0A59F7 0%, #337BF7 100%);
  border-radius: 20px 0 0 20px;
  transition: none;
}

.slider-captcha__thumb {
  position: absolute;
  top: 2px;
  width: 36px;
  height: 36px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  font-size: 16px;
  color: #666;
  transition: none;
}

.slider-captcha__text {
  position: absolute;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #999;
  pointer-events: none;
}

.slider-captcha__refresh {
  text-align: center;
  margin-top: 6px;
  cursor: pointer;
  font-size: 18px;
  color: #999;
}

.slider-captcha__refresh:hover {
  color: #0A59F7;
}
</style>
