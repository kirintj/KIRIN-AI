<script setup lang="ts">
import TheIcon from '@/components/icon/TheIcon.vue'
import { NPopconfirm, NInput } from 'naive-ui'
import { formatRelativeTime } from '@/utils/common/time'
import { ref } from 'vue'

const props = defineProps<{
  conversations: any[]
  filteredConversations: any[]
  groupedConversations: any[]
  currentConversationId: string | null
  searchKeyword: string
}>()

const emit = defineEmits<{
  (e: 'update:searchKeyword', val: string): void
  (e: 'switch', id: string): void
  (e: 'new'): void
  (e: 'delete', id: string): void
  (e: 'rename', id: string, title: string): void
}>()

const renamingId = ref<string | null>(null)
const renameValue = ref('')

const startRename = (convId: string, currentTitle: string) => {
  renamingId.value = convId
  renameValue.value = currentTitle
}

const confirmRename = () => {
  if (renamingId.value && renameValue.value.trim()) {
    emit('rename', renamingId.value, renameValue.value.trim())
  }
  renamingId.value = null
}

const cancelRename = () => {
  renamingId.value = null
}
</script>

<template>
  <div class="hm-sidebar-inner">
    <div class="hm-sidebar-header">
      <span class="hm-sidebar-title">对话</span>
      <button class="hm-sidebar-new-btn" @click="emit('new')">
        <TheIcon icon="icon-park-outline:plus" :size="16" />
      </button>
    </div>

    <div class="hm-sidebar-search">
      <div class="hm-search-box">
        <TheIcon icon="icon-park-outline:search" :size="14" color="var(--hm-font-fourth)" />
        <input
          :value="searchKeyword"
          class="hm-search-input"
          placeholder="搜索对话..."
          @input="emit('update:searchKeyword', ($event.target as HTMLInputElement).value)"
        />
        <button v-if="searchKeyword" class="hm-search-clear" @click="emit('update:searchKeyword', '')">
          <TheIcon icon="icon-park-outline:close" :size="12" />
        </button>
      </div>
    </div>

    <div class="hm-sidebar-list">
      <template v-for="group in groupedConversations" :key="group.label">
        <div class="hm-sidebar-group-label">{{ group.label }}</div>
        <div
          v-for="conv in group.items"
          :key="conv.id"
          :class="['hm-sidebar-item', { active: conv.id === currentConversationId }]"
          @click="emit('switch', conv.id)"
        >
          <TheIcon icon="icon-park-outline:chat" :size="16" class="hm-conv-icon" />
          <div v-if="renamingId === conv.id" class="hm-conv-rename" @click.stop>
            <NInput
              v-model:value="renameValue"
              size="tiny"
              placeholder="输入新名称"
              @keyup.enter="confirmRename"
              @keyup.escape="cancelRename"
              @blur="confirmRename"
              autofocus
            />
          </div>
          <div v-else class="hm-conv-info">
            <div class="hm-conv-title">{{ conv.title || '新对话' }}</div>
            <div class="hm-conv-meta">{{ conv.message_count || 0 }} 条消息 · {{ formatRelativeTime(conv.updated_at) }}</div>
          </div>
          <div class="hm-conv-actions" @click.stop>
            <button class="hm-conv-action" @click="startRename(conv.id, conv.title)">
              <TheIcon icon="icon-park-outline:edit" :size="12" />
            </button>
            <NPopconfirm @positive-click="emit('delete', conv.id)">
              <template #trigger>
                <button class="hm-conv-action danger">
                  <TheIcon icon="icon-park-outline:delete" :size="12" />
                </button>
              </template>
              确定删除该对话？
            </NPopconfirm>
          </div>
        </div>
      </template>

      <div v-if="conversations.length === 0" class="hm-sidebar-empty">
        <TheIcon icon="icon-park-outline:chat" :size="32" color="var(--hm-font-fourth)" />
        <p>暂无对话</p>
      </div>

      <div v-if="conversations.length > 0 && filteredConversations.length === 0" class="hm-sidebar-empty">
        <TheIcon icon="icon-park-outline:search" :size="32" color="var(--hm-font-fourth)" />
        <p>未找到匹配的对话</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hm-sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.hm-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  flex-shrink: 0;
}

.hm-sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--hm-font-primary);
}

.hm-sidebar-new-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--hm-radius-sm);
  border: 1px solid var(--hm-border);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-secondary);
  transition: all 0.25s var(--hm-spring);
}

.hm-sidebar-new-btn:hover {
  border-color: var(--hm-brand);
  color: var(--hm-brand);
  background: var(--hm-brand-light);
  transform: scale(1.05);
}

.hm-sidebar-search {
  padding: 8px 12px;
  flex-shrink: 0;
}

.hm-search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-md);
  transition: border-color 0.25s;
}

.hm-search-box:focus-within {
  border-color: var(--hm-brand);
}

.hm-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--hm-font-primary);
  min-width: 0;
}

.hm-search-input::placeholder {
  color: var(--hm-font-fourth);
}

.hm-search-clear {
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-fourth);
  transition: all 0.25s var(--hm-spring);
}

.hm-search-clear:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--hm-font-primary);
  transform: scale(1.1);
}

.hm-sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px 8px;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.hm-sidebar-list::-webkit-scrollbar { display: none; }

.hm-sidebar-group-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--hm-font-fourth);
  padding: 10px 12px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hm-sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--hm-radius-md);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
  position: relative;
}

.hm-sidebar-item:hover {
  background: rgba(10, 89, 247, 0.04);
  transform: translateX(2px);
}

.hm-sidebar-item.active {
  background: var(--hm-brand-light);
}

.hm-conv-icon {
  flex-shrink: 0;
  color: var(--hm-font-tertiary);
  transition: transform 0.3s var(--hm-spring);
}

.hm-sidebar-item:hover .hm-conv-icon {
  transform: scale(1.1);
}

.hm-sidebar-item.active .hm-conv-icon {
  color: var(--hm-brand);
}

.hm-conv-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.hm-conv-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--hm-font-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-conv-meta {
  font-size: 11px;
  color: var(--hm-font-fourth);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hm-conv-rename {
  flex: 1;
  min-width: 0;
}

.hm-conv-actions {
  display: none;
  gap: 2px;
  flex-shrink: 0;
}

.hm-sidebar-item:hover .hm-conv-actions {
  display: flex;
}

.hm-conv-action {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--hm-radius-sm);
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--hm-font-fourth);
  transition: all 0.25s var(--hm-spring);
}

.hm-conv-action:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--hm-font-primary);
  transform: scale(1.1);
}

.hm-conv-action.danger:hover {
  background: rgba(232, 64, 38, 0.08);
  color: #E84026;
}

.hm-sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.hm-sidebar-empty p {
  font-size: 13px;
  color: var(--hm-font-fourth);
  margin-top: 8px;
}
</style>
