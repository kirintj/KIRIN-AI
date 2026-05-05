<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useMarkdown } from '@/composables/useMarkdown'

const props = defineProps<{
  list: Array<{ role: string; content: string }>;
  isLoading?: boolean;
}>();

const { formatMessage, scrollToBottom } = useMarkdown()

const handleCodeToggle = (e: Event) => {
  const target = e.target as HTMLElement;
  const btn = target.closest('.code-toggle') as HTMLElement;
  if (!btn) return;

  const codeId = btn.dataset.target;
  const codeBody = document.getElementById(codeId!);
  if (!codeBody) return;

  const isCollapsed = btn.dataset.collapsed === 'true';
  btn.dataset.collapsed = isCollapsed ? 'false' : 'true';
  const toggleText = btn.querySelector('.toggle-text');
  const toggleIcon = btn.querySelector('.toggle-icon');

  if (isCollapsed) {
    codeBody.style.maxHeight = codeBody.scrollHeight + 'px';
    codeBody.style.opacity = '1';
    if (toggleText) toggleText.textContent = '收起';
    if (toggleIcon) (toggleIcon as HTMLElement).style.transform = 'rotate(0deg)';
  } else {
    codeBody.style.maxHeight = '0px';
    codeBody.style.opacity = '0';
    if (toggleText) toggleText.textContent = '展开';
    if (toggleIcon) (toggleIcon as HTMLElement).style.transform = 'rotate(-90deg)';
  }
};

watch(
  () => props.list,
  () => { scrollToBottom('.message-list') },
  { deep: true }
)

onMounted(() => {
  scrollToBottom('.message-list')
  document.addEventListener('click', handleCodeToggle);
})
</script>

<template>
  <div ref="messageRef" class="message-container">
    <div class="message-list cus-scroll-y">
      <div v-if="list.length === 0" class="flex flex-col items-center justify-center h-full">
        <p class="text-center font-bold text-40 ">开始聊天吧</p>
      </div>

      <div
        v-for="(item, index) in list"
        :key="index"
        :class="['message-item', item.role === 'user' ? 'send' : 'receive']"
      >
        <div
          v-html="formatMessage(item.content, item.role)"
          class="message-bubble md-bubble max-w-none"
        ></div>
      </div>

      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner">
          <div class="spinner"></div>
          <span class="loading-text">正在思考...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-container {
  width: 100%;
  height: 100vh;
  overflow-y: auto;
  scroll-behavior: smooth;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.message-container::-webkit-scrollbar { display: none; }

.cus-scroll-y {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.cus-scroll-y::-webkit-scrollbar { display: none; }

.message-list {
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 8px;
  padding-left: 12px;
  padding-right: 12px;
  padding-bottom: 20px;
  width: 60%;
  height: 100%;
}

.message-item { display: flex; width: 100%; align-items: start; }
.message-item.receive { justify-content: flex-start; }
.message-item.send { justify-content: flex-end; }

.message-bubble {
  padding: 8px 12px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-all;
  width: auto;
}
.receive .message-bubble { width: 100%; font-size: 14px; }
.send .message-bubble {
  font-size: 14px;
  background: #1890ff;
  color: #fff;
  max-width: 60%;
}

/* 代码块折叠功能样式 */
:deep(.message-bubble .code-block) {
  margin: 12px 0;
  border-radius: 10px;
  overflow: hidden;
  background: #fafafa;
  border: 1px solid #e8e8e8;
}

:deep(.message-bubble .code-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: #f0f0f0;
  border-bottom: 1px solid #e8e8e8;
}

:deep(.message-bubble .code-lang) {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

:deep(.message-bubble .code-toggle) {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  color: #888;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  line-height: 1;
}
:deep(.message-bubble .code-toggle:hover) {
  background: rgba(0, 0, 0, 0.08); color: #555;
}
:deep(.message-bubble .toggle-icon) { transition: transform 0.25s ease; }
:deep(.message-bubble .toggle-text) { font-size: 11px; }

:deep(.message-bubble .code-body) {
  max-height: 600px;
  overflow: hidden;
  opacity: 1;
  transition: max-height 0.3s ease, opacity 0.25s ease;
}

:deep(.message-bubble .code-body pre) {
  margin: 0;
  padding: 14px;
  overflow-x: auto;
  background: #fff;
  line-height: 1.6 !important;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}
:deep(.message-bubble .code-body pre::-webkit-scrollbar) { height: 4px; width: 4px; }
:deep(.message-bubble .code-body pre::-webkit-scrollbar-track) { background: transparent; }
:deep(.message-bubble .code-body pre::-webkit-scrollbar-thumb) { background: rgba(0, 0, 0, 0.12); border-radius: 2px; }
:deep(.message-bubble .code-body pre::-webkit-scrollbar-thumb:hover) { background: rgba(0, 0, 0, 0.22); }

:deep(.message-bubble .code-body pre code) {
  padding: 0 !important;
  margin: 0 !important;
  font-size: 13px !important;
  line-height: 1.6 !important;
  background: transparent !important;
  color: #333;
  font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace;
}
</style>
