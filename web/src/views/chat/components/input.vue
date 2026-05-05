<script setup lang="ts">
import { ref } from 'vue'
import TheIcon from '@/components/icon/TheIcon.vue'

const message = ref('')
const model = ref('qwen-turbo-2025-04-28')
const temperature = ref(0.7)
const maxTokens = ref(2000)
const stream = ref(false) // 流式开关
const emit = defineEmits(['send'])

const sendMessage = () => {
  if (!message.value.trim()) return
  emit('send', message.value, model.value, temperature.value, maxTokens.value, stream.value)
  message.value = ''
}

// 切换流式输出
const toggleStream = () => {
  stream.value = !stream.value
}
</script>

<template>
  <div class="chat-input">
    <div class="floating-chatbox">
      <div class="input-wrapper">
        <input
          v-model="message"
          class="input-box"
          placeholder="输入消息..."
          required
          @keyup.enter="sendMessage"
        />
      </div>

      <div class="button-group">
        <div>
          <!-- 流式输出按钮修复 -->
          <button :class="['btn', { active: stream }]" type="button" @click="toggleStream">
            <TheIcon icon="icon-park-outline:aquarius" :size="18" class="mr-5" />
            {{ stream ? '流式输出：开' : '流式输出' }}
          </button>

          <button class="btn" type="button">
            <TheIcon icon="icon-park-outline:link-two" :size="18" class="mr-5" />
            上传文件
          </button>
        </div>

        <button
          class="submit-button"
          type="button"
          :disabled="!message.trim()"
          @click="sendMessage"
        >
          <TheIcon icon="icon-park-outline:arrow-up" :size="18" :color="'white'"/>
        </button>
      </div>
    </div>
    <!-- 模糊遮罩 -->
    <div class="blur-overlay"></div>
  </div>
</template>

<style scoped>
.chat-input{
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100px;
  padding-bottom: 24px;
  background: transparent;
  position: relative;
}

.floating-chatbox {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: 1px solid #007DFF;
  border-radius: 24px;
  padding: 12px 16px;;
  font-size: 16px;
  color: #303133;
  width: 60%;
  height: 100px;
  
  /* 毛玻璃模糊效果 + 柔和蓝色发光 */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(1px);
  box-shadow: 0 0 18px rgba(0, 125, 255, 0.25);
}

.button-group {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submit-button {
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: not-allowed;
  transition: background 0.2s;
}

.input-wrapper:has(.input-box:valid)+.button-group .submit-button {
  background: #007DFF;
  cursor: pointer;
}
.input-wrapper:has(.input-box:valid) + .button-group .submit-button .icon {
  color: white;
}

.input-box {
  width: 100%;
  border: none;
  outline: none;
  padding: 4px 0;
  background: transparent;
}

.btn {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #007DFF;
  border-radius: 24px;
  padding: 4px 12px;
  font-size: 14px;
  margin-right: 6px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  cursor: pointer;
  transition: all 0.2s;
}

.btn.active {
  background: #007DFF;
  color: #fff;
}

/* 模糊遮罩 */
.blur-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120px;
  background: linear-gradient(to top, rgba(255, 255, 255, 0.8), transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: -1;
}
</style>