<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NForm, NFormItem, NInput, NInputNumber, NSwitch, NSpace, NTooltip } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'

const { t } = useI18n()

defineOptions({ name: 'AI模型配置' })

const loading = ref(false)
const saving = ref(false)

const formData = ref({
  model_name: '',
  api_key: '',
  base_url: '',
  max_tokens: 2000,
  temperature: 0.7,
  embedding_model: '',
  embedding_dimension: 1024,
  embedding_api_key: '',
  embedding_base_url: '',
  rerank_api_key: '',
  rerank_base_url: '',
  rerank_model: '',
  rag_enable_query_rewrite: true,
  rag_enable_rerank: true,
  rag_enable_hybrid_search: true,
  rag_enable_context_compress: false,
})

async function loadConfig() {
  loading.value = true
  try {
    const res = await api.getAiConfig()
    const data = res.data
    formData.value = {
      model_name: data.model_name || '',
      api_key: data.api_key || '',
      base_url: data.base_url || '',
      max_tokens: parseInt(data.max_tokens) || 2000,
      temperature: parseFloat(data.temperature) || 0.7,
      embedding_model: data.embedding_model || '',
      embedding_dimension: parseInt(data.embedding_dimension) || 1024,
      embedding_api_key: data.embedding_api_key || '',
      embedding_base_url: data.embedding_base_url || '',
      rerank_api_key: data.rerank_api_key || '',
      rerank_base_url: data.rerank_base_url || '',
      rerank_model: data.rerank_model || '',
      rag_enable_query_rewrite: data.rag_enable_query_rewrite === 'true',
      rag_enable_rerank: data.rag_enable_rerank === 'true',
      rag_enable_hybrid_search: data.rag_enable_hybrid_search === 'true',
      rag_enable_context_compress: data.rag_enable_context_compress === 'true',
    }
  } catch (err) {
    $message.error(t('views.system.ai_config.msg_load_failed'))
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const configs = [
      { key: 'model_name', value: formData.value.model_name, desc: t('views.system.ai_config.desc_model') },
      { key: 'api_key', value: formData.value.api_key, desc: t('views.system.ai_config.desc_api_key') },
      { key: 'base_url', value: formData.value.base_url, desc: t('views.system.ai_config.desc_base_url') },
      { key: 'max_tokens', value: String(formData.value.max_tokens), desc: t('views.system.ai_config.desc_max_tokens') },
      { key: 'temperature', value: String(formData.value.temperature), desc: t('views.system.ai_config.desc_temperature') },
      { key: 'embedding_model', value: formData.value.embedding_model, desc: t('views.system.ai_config.desc_embedding_model') },
      { key: 'embedding_dimension', value: String(formData.value.embedding_dimension), desc: t('views.system.ai_config.desc_embedding_dim') },
      { key: 'embedding_api_key', value: formData.value.embedding_api_key, desc: t('views.system.ai_config.desc_embedding_api_key') },
      { key: 'embedding_base_url', value: formData.value.embedding_base_url, desc: t('views.system.ai_config.desc_embedding_base_url') },
      { key: 'rerank_api_key', value: formData.value.rerank_api_key, desc: t('views.system.ai_config.desc_rerank_api_key') },
      { key: 'rerank_base_url', value: formData.value.rerank_base_url, desc: t('views.system.ai_config.desc_rerank_base_url') },
      { key: 'rerank_model', value: formData.value.rerank_model, desc: t('views.system.ai_config.desc_rerank_model') },
      { key: 'rag_enable_query_rewrite', value: String(formData.value.rag_enable_query_rewrite), desc: t('views.system.ai_config.desc_query_rewrite') },
      { key: 'rag_enable_rerank', value: String(formData.value.rag_enable_rerank), desc: t('views.system.ai_config.desc_rerank') },
      { key: 'rag_enable_hybrid_search', value: String(formData.value.rag_enable_hybrid_search), desc: t('views.system.ai_config.desc_hybrid') },
      { key: 'rag_enable_context_compress', value: String(formData.value.rag_enable_context_compress), desc: t('views.system.ai_config.desc_context_compress') },
    ]
    await api.updateAiConfig({ configs })
    $message.success(t('views.system.ai_config.msg_save_success'))
  } catch (err) {
    $message.error(t('views.system.ai_config.msg_save_failed'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <CommonPage show-footer :title="t('views.system.ai_config.page_title')">
    <template #action>
      <button class="hm-action-btn primary" :disabled="saving" @click="handleSave">
        <TheIcon icon="material-symbols:save" :size="16" color="#fff" />
        {{ saving ? t('views.system.ai_config.btn_saving') : t('views.system.ai_config.btn_save') }}
      </button>
    </template>

    <NSpin :show="loading">
      <div class="hm-config-sections">
        <!-- LLM 模型配置 -->
        <div class="hm-config-card">
          <h3 class="hm-section-title">{{ t('views.system.ai_config.section_llm') }}</h3>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem :label="t('views.system.ai_config.form_model')">
              <NInput
                v-model:value="formData.model_name"
                :placeholder="t('views.system.ai_config.model_placeholder')"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_api_key')">
              <NInput
                v-model:value="formData.api_key"
                :placeholder="t('views.system.ai_config.api_key_placeholder')"
                type="password"
                show-password-on="click"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_base_url')">
              <NInput
                v-model:value="formData.base_url"
                :placeholder="t('views.system.ai_config.base_url_placeholder')"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_max_tokens')">
              <NInputNumber
                v-model:value="formData.max_tokens"
                :min="100"
                :max="32000"
                :step="100"
                style="width: 100%"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_temperature')">
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

        <!-- RAG 配置 -->
        <div class="hm-config-card">
          <h3 class="hm-section-title">{{ t('views.system.ai_config.section_rag') }}</h3>

          <!-- Embedding 子区块 -->
          <h4 class="hm-sub-title">{{ t('views.system.ai_config.sub_embedding') }}</h4>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem :label="t('views.system.ai_config.form_embedding_model')">
              <NInput
                v-model:value="formData.embedding_model"
                :placeholder="t('views.system.ai_config.embedding_placeholder')"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_embedding_dim')">
              <NInputNumber
                v-model:value="formData.embedding_dimension"
                :min="256"
                :max="4096"
                :step="256"
                style="width: 100%"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_embedding_api_key')">
              <NInput
                v-model:value="formData.embedding_api_key"
                :placeholder="t('views.system.ai_config.embedding_api_key_placeholder')"
                type="password"
                show-password-on="click"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_embedding_base_url')">
              <NInput
                v-model:value="formData.embedding_base_url"
                :placeholder="t('views.system.ai_config.embedding_base_url_placeholder')"
              />
            </NFormItem>
          </NForm>

          <!-- Rerank 子区块 -->
          <h4 class="hm-sub-title">{{ t('views.system.ai_config.sub_rerank') }}</h4>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem :label="t('views.system.ai_config.form_rerank_model')">
              <NInput
                v-model:value="formData.rerank_model"
                :placeholder="t('views.system.ai_config.rerank_model_placeholder')"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_rerank_api_key')">
              <NInput
                v-model:value="formData.rerank_api_key"
                :placeholder="t('views.system.ai_config.rerank_api_key_placeholder')"
                type="password"
                show-password-on="click"
              />
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_rerank_base_url')">
              <NInput
                v-model:value="formData.rerank_base_url"
                :placeholder="t('views.system.ai_config.rerank_base_url_placeholder')"
              />
            </NFormItem>
          </NForm>

          <!-- 检索策略子区块 -->
          <h4 class="hm-sub-title">{{ t('views.system.ai_config.sub_strategy') }}</h4>
          <NForm label-placement="left" label-align="left" :label-width="120">
            <NFormItem :label="t('views.system.ai_config.form_query_rewrite')">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_query_rewrite" />
                <span class="hm-config-hint">{{ t('views.system.ai_config.query_rewrite_hint') }}</span>
              </NSpace>
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_hybrid')">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_hybrid_search" />
                <span class="hm-config-hint">{{ t('views.system.ai_config.hybrid_hint') }}</span>
              </NSpace>
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_rerank')">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_rerank" />
                <span class="hm-config-hint">{{ t('views.system.ai_config.rerank_hint') }}</span>
              </NSpace>
            </NFormItem>
            <NFormItem :label="t('views.system.ai_config.form_context_compress')">
              <NSpace align="center">
                <NSwitch v-model:value="formData.rag_enable_context_compress" />
                <span class="hm-config-hint">{{ t('views.system.ai_config.context_compress_hint') }}</span>
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

.hm-sub-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--hm-font-secondary);
  margin: 16px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--hm-border-glass);
}

.hm-sub-title:first-of-type {
  margin-top: 0;
}

.hm-config-hint {
  font-size: 12px;
  color: var(--hm-font-fourth);
}
</style>
