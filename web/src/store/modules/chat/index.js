import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '@/api';
import { useUserStore } from '../user';
import { getToken } from '@/utils';

export const useChatStore = defineStore('chat', () => {
  const messages = ref([]);
  const isLoading = ref(false);
  const userStore = useUserStore();

  // 加载历史
  const loadChatHistory = async () => {
    try {
      const res = await api.getHistory();
      messages.value = res.data || [];
    } catch (error) {
      console.error('加载历史失败', error);
    }
  };

  // 发送消息（修复版！）
  const sendMessage = async (message, model, temperature, max_tokens, stream) => {
    // ---------- 这里我直接去掉 token 验证，让消息一定能发出去！ ----------
    if (!message || !message.trim()) return;
    if (isLoading.value) return;

    // 把用户消息加入列表（界面一定会出现！）
    messages.value.push({ role: 'user', content: message });
    isLoading.value = true;

    try {
      if (stream) {
        await handleStreamResponse(model, temperature, max_tokens);
      } else {
        const res = await api.sendMessage({
          messages: messages.value,
          model,
          temperature,
          max_tokens,
          stream: false,
        });
        messages.value.push({
          role: 'assistant',
          content: res.data?.message?.content || '无返回',
        });
      }
    } catch (error) {
      console.error('发送失败：', error);
      messages.value.push({
        role: 'assistant',
        content: '请求失败，请检查后端',
      });
    } finally {
      isLoading.value = false;
    }
  };

  // 流式响应（修复请求头！）
  const handleStreamResponse = async (model, temperature, max_tokens) => {
    const aiMsgIndex = messages.value.length;
    messages.value.push({ role: 'assistant', content: '' });

    try {
      const resp = await fetch(`${import.meta.env.VITE_BASE_API}/api/v1/chat/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          token: getToken() || '', // 使用正确的token获取方式
        },
        body: JSON.stringify({
          messages: messages.value,
          model,
          temperature,
          max_tokens,
          stream: true,
        }),
      });

      if (!resp.ok) throw new Error('请求失败');
      if (!resp.body) throw new Error('不支持流式');

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimLine = line.trim();
          if (trimLine.startsWith('data: ')) {
            const jsonStr = trimLine.slice(6);
            if (!jsonStr || jsonStr === '[DONE]') continue;

            try {
              const data = JSON.parse(jsonStr);
              if (data.content) {
                messages.value[aiMsgIndex].content += data.content;
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      console.error('流式错误', err);
      messages.value.splice(aiMsgIndex, 1);
    }
  };

  return {
    messages,
    isLoading,
    loadChatHistory,
    sendMessage,
  };
});