<script setup>
import { onMounted, ref } from 'vue'
import { NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NSpace, NTooltip } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'

defineOptions({ name: 'AI模型配置' })

const loading = ref(false)
const saving = ref(false)

const formData = ref({
  model_name: 'qwen-turbo',
  max_tokens: 2000,
  temperature: 0.7,
  embedding_model: 'text-embedding-v3',
  embedding_dimension: 1024,
  rag_enable_query_rewrite: true,
  rag_enable_rerank: true,
  rag_enable_hybrid_search: true,
  rag_enable_context_compress: false,
})

const modelOptions = [
  { label: 'qwen-turbo', value: 'qwen-turbo' },
  { label: 'qwen-plus', value: 'qwen-plus' },
  { label: 'qwen-max', value: 'qwen-max' },
  { label: 'qwen-long', value: 'qwen-long' },
]

const embeddingModelOptions = [
  { label: 'text-embedding-v3', value: 'text-embedding-v3' },
  { label: 'text-embedding-v2', value: 'text-embedding-v2' },
]

async function loadConfig() {
  loading.value = true
  try {
    const res = await api.getAiConfig()
    const data = res.data
    formData.value = {
      model_name: data.model_name || 'qwen-turbo',
      max_tokens: parseInt(data.max_tokens) || 2000,
      temperature: parseFloat(data.temperature) || 0.7,
      embedding_model: data.embedding_model || 'text-embedding-v3',
      embedding_dimension: parseInt(data.embedding_dimension) || 1024,
      rag_enable_query_rewrite: data.rag_enable_query_rewrite === 'true',
      rag_enable_rerank: data.rag_enable_rerank === 'true',
      rag_enable_hybrid_search: data.rag_enable_hybrid_search === 'true',
      rag_enable_context_compress: data.rag_enable_context_compress === 'true',
    }
  } catch (err) {
    $message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const configs = [
      { key: 'model_name', value: formData.value.model_name, desc: 'LLM 模型名称' },
      { key: 'max_tokens', value: String(formData.value.max_tokens), desc: '最大生成 Token 数' },
      { key: 'temperature', value: String(formData.value.temperature), desc: '生成温度' },
      { key: 'embedding_model', value: formData.value.embedding_model, desc: 'Embedding 模型名称' },
      { key: 'embedding_dimension', value: String(formData.value.embedding_dimension), desc: 'Embedding 维度' },
      { key: 'rag_enable_query_rewrite', value: String(formData.value.rag_enable_query_rewrite), desc: '启用查询改写' },
      { key: 'rag_enable_rerank', value: String(formData.value.rag_enable_rerank), desc: '启用重排序' },
      { key: 'rag_enable_hybrid_search', value: String(formData.value.rag_enable_hybrid_search), desc: '启用混合检索' },
      { key: 'rag_enable_context_compress', value: String(formData.value.rag_enable_context_compress), desc: '启用上下文压缩' },
    ]
    await api.updateAiConfig({ configs })
    $message.success('配置保存成功')
  } catch (err) {
    $message.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <CommonPage show-footer title="AI 模型配置">
    <template #action>
      <button class="hm-action-btn primary" :disabled="saving" @click="handleSave">
        <TheIcon icon="material-symbols:save" :size="16" color="#fff" />
        {{ saving ? '保存中...' : '保存配置' }}
      </button>
    </template>

    <NSpin :show="loading">
      <div class="hm-config-sections">
        <div class="hm-config-card">
          <h3 class="hm-section-title">LLM 模型配置</h3>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem label="模型名称">
              <NSelect
                v-model:value="formData.model_name"
                :options="modelOptions"
                placeholder="选择模型"
                filterable
                tag
              />
            </NFormItem>
            <NFormItem label="最大 Token 数">
              <NInputNumber
                v-model:value="formData.max_tokens"
                :min="100"
                :max="32000"
                :step="100"
                style="width: 100%"
              />
            </NFormItem>
            <NFormItem label="温度 (Temperature)">
              <NInputNumber
                v-model:value="formData.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </NFormItem>
          </NForm>
        </div>

        <div class="hm-config-card">
          <h3 class="hm-section-title">Embedding 配置</h3>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem label="Embedding 模型">
              <NSelect
                v-model:value="formData.embedding_model"
                :options="embeddingModelOptions"
                placeholder="选择 Embedding 模型"
                filterable
                tag
              />
            </NFormItem>
            <NFormItem label="Embedding 维度">
              <NInputNumber
                v-model:value="formData.embedding_dimension"
                :min="256"
                :max="4096"
                :step="256"
                style="width: 100%"
              />
            </NFormItem>
          </NForm>
        </div>

        <div class="hm-config-card">
          <h3 class="hm-section-title">RAG 配置</h3>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem label="查询改写">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_query_rewrite" />
                <span class="hm-config-hint">将用户查询改写为更适合检索的形式</span>
              </NSpace>
            </NFormItem>
            <NFormItem label="重排序">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_rerank" />
                <span class="hm-config-hint">对检索结果进行重排序提升相关性</span>
              </NSpace>
            </NFormItem>
            <NFormItem label="混合检索">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_hybrid_search" />
                <span class="hm-config-hint">同时使用向量检索和关键词检索</span>
              </NSpace>
            </NFormItem>
            <NFormItem label="上下文压缩">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_context_compress" />
                <span class="hm-config-hint">压缩检索上下文减少 Token 消耗</span>
              </NSpace>
            </NFormItem>
          </NForm>
        </div>
      </div>
    </NSpin>
  </CommonPage>
</template>

<style scoped>
.hm-config-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hm-config-card {
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass);
  -webkit-backdrop-filter: var(--hm-blur-glass);
  border: 1px solid var(--hm-border-glass);
  border-radius: var(--hm-radius-xl);
  box-shadow: var(--hm-shadow-layered);
  padding: 20px 24px;
}

.hm-config-hint {
  font-size: 12px;
  color: var(--hm-font-fourth);
}
</style>
