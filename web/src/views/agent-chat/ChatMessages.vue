<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'
import LoadingDots from '@/components/common/LoadingDots.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useMarkdown } from '@/composables/useMarkdown'
import { formatMsgTime, shouldShowTimeDivider } from '@/utils/common/time'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AgentMessage } from '@/types/chat'

const props = defineProps<{
  messages: AgentMessage[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'regenerate', index: number): void
}>()

const { t } = useI18n()
const { formatMessage, scrollToBottom } = useMarkdown()
const copiedId = ref<string | null>(null)
const feedbackMap = ref<Record<string, 'like' | 'dislike'>>({})

const copyMessage = async (content: string, id: string) => {
  try {
    await navigator.clipboard.writeText(content)
    copiedId.value = id
    setTimeout(() => { copiedId.value = null }, 1500)
  } catch {
    window.$message?.error(t('views.agent_chat.msg_copy_failed'))
  }
}

const toggleFeedback = (id: string, type: 'like' | 'dislike') => {
  feedbackMap.value[id] = feedbackMap.value[id] === type ? undefined as any : type
}

defineExpose({ scrollToBottom })
</script>

<template>
  <div class="hm-msg-list">
    <EmptyState
      v-if="messages.length === 0"
      icon="icon-park-outline:robot"
      :title="t('views.agent_chat.empty_title')"
    />

    <template v-for="(item, index) in messages" :key="item.id">
      <div v-if="shouldShowTimeDivider(messages, index)" class="hm-msg-time-divider">
        {{ formatMsgTime(item.timestamp) }}
      </div>
      <div :class="['hm-msg-item', item.role]">
        <div class="hm-msg-content">
          <div class="hm-msg-bubble-wrap">
            <div v-html="formatMessage(item.content, item.role)" class="hm-msg-bubble md-bubble"></div>
          </div>
          <div v-if="item.role === 'assistant'" class="hm-msg-actions">
            <button class="hm-msg-action" @click="copyMessage(item.content, item.id)">
              <TheIcon
                :icon="copiedId === item.id ? 'icon-park-outline:success' : 'icon-park-outline:copy'"
                :size="12"
                :color="copiedId === item.id ? '#64BB5C' : 'var(--hm-font-fourth)'"
              />
              {{ copiedId === item.id ? t('common.actions.copied') : t('common.actions.copy') }}
            </button>
            <button class="hm-msg-action" @click="emit('regenerate', index)" :disabled="isLoading">
              <TheIcon icon="icon-park-outline:refresh" :size="12" color="var(--hm-font-fourth)" />
              {{ t('views.agent_chat.btn_regenerate') }}
            </button>
            <button
              :class="['hm-msg-action', { active: feedbackMap[item.id] === 'like' }]"
              @click="toggleFeedback(item.id, 'like')"
            >
              <TheIcon
                icon="icon-park-outline:like"
                :size="12"
                :color="feedbackMap[item.id] === 'like' ? '#0A59F7' : 'var(--hm-font-fourth)'"
              />
            </button>
            <button
              :class="['hm-msg-action', { active: feedbackMap[item.id] === 'dislike' }]"
              @click="toggleFeedback(item.id, 'dislike')"
            >
              <TheIcon
                icon="icon-park-outline:dislike"
                :size="12"
                :color="feedbackMap[item.id] === 'dislike' ? '#E84026' : 'var(--hm-font-fourth)'"
              />
            </button>
          </div>
        </div>
      </div>
    </template>

    <div v-if="isLoading" class="hm-msg-item assistant">
      <LoadingDots :text="t('views.agent_chat.thinking')" />
    </div>
  </div>
</template>

<style scoped>
.hm-msg-list {
  max-width: 70%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 16px;
  height: 100%;
  overflow-y: auto;
  scroll-behavior: smooth;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.hm-msg-list::-webkit-scrollbar { display: none; }

.hm-msg-time-divider {
  text-align: center;
  font-size: 11px;
  color: var(--hm-font-fourth);
  padding: 4px 0;
}

.hm-msg-item {
  display: flex;
  width: 100%;
  align-items: flex-start;
  gap: 10px;
  animation: hm-msg-in 0.35s var(--hm-spring);
}

.hm-msg-item.user {
  justify-content: flex-end;
}

.hm-msg-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hm-msg-bubble-wrap {
  display: inline-flex;
  align-items: flex-end;
  gap: 0;
  min-width: 0;
  max-width: 100%;
}

.hm-msg-bubble {
  padding: 10px 14px;
  border-radius: var(--hm-radius-lg);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  min-width: 0;
  overflow: hidden;
}

.assistant .hm-msg-bubble {
  backdrop-filter: var(--hm-blur-glass);
  /* border: 1px solid var(--hm-border-glass); */
  color: var(--hm-font-primary);
  max-width: 100%;
}

.user .hm-msg-bubble {
  background: var(--hm-brand-gradient);
  color: var(--hm-font-on-brand);
  max-width: 100%;
  box-shadow: var(--hm-shadow-brand);
}

.hm-msg-actions {
  display: flex;
  gap: 4px;
  padding-left: 4px;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.3s var(--hm-spring);
}

.hm-msg-item:hover .hm-msg-actions {
  opacity: 1;
  transform: translateY(0);
}

.hm-msg-action {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  font-size: 11px;
  color: var(--hm-font-fourth);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
}

.hm-msg-action:hover {
  background: var(--hm-hover-bg);
  color: var(--hm-font-secondary);
  transform: translateY(-1px);
}

.hm-msg-action.active {
  background: var(--hm-brand-bg-light);
}

.hm-msg-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes hm-msg-in {
  from { opacity: 0; transform: translateY(12px) scale(0.97); filter: blur(2px); }
  to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
</style>
