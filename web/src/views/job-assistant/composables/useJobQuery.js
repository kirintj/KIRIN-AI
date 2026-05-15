import { ref } from 'vue'
import i18n from '~/i18n'

const t = i18n.global.t

export function useJobQuery(apiFn, extractField = '') {
  const loading = ref(false)
  const result = ref('')

  const execute = async (params, errorMsg = t('views.job_assistant.msg_generation_failed')) => {
    loading.value = true
    result.value = ''
    try {
      const res = await apiFn(params)
      result.value = extractField ? (res.data?.[extractField] || '') : (res.data || '')
    } catch (error) {
      window.$message?.error(error?.message || errorMsg)
    } finally {
      loading.value = false
    }
  }

  const reset = () => {
    result.value = ''
  }

  return { loading, result, execute, reset }
}
