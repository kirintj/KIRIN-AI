<script setup lang="ts">
import { useUserStore } from '@/store/modules/user';
import { useChatStore } from '../../store/modules/chat';
import { useRouter } from 'vue-router';
import Input from './components/input.vue';  
import ChatView from './components/chatview.vue';
import { useMarkdown } from '@/composables/useMarkdown';
import { onMounted, watch } from 'vue';

const userStore = useUserStore();
const chatStore = useChatStore();
const router = useRouter();
const { formatMessage, scrollToBottom } = useMarkdown();

if (!userStore.userId) {
  router.push('/');
}

// 处理发送消息
const handleSend = (val: string, model?: string, temperature?: number, maxTokens?: number, stream?: boolean) => {
  chatStore.sendMessage(val, model, temperature, maxTokens, stream);
};

onMounted(() => {
  chatStore.loadChatHistory().then(() => scrollToBottom('.message-container'));
});

watch(
  () => chatStore.messages,
  () => scrollToBottom('.message-container'),
  { deep: true }
);
</script>

<template>
  <AppPage :show-footer="false">
    <div class="chat-page" flex-1 flex flex-col relative>
      <!-- 聊天消息区域 -->
      <ChatView 
        :list="chatStore.messages" 
        :formatMessage="formatMessage" 
        :isLoading="chatStore.isLoading"
      />
      <!-- 输入框区域 -->
      <Input @send="handleSend" />
    </div>
  </AppPage>
</template>

<style scoped>
.chat-page {
  height: 100vh;
  overflow: hidden;
}
</style>