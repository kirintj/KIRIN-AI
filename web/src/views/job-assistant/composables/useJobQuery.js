import { ref } from 'vue'

export function useJobQuery(apiFn, extractField = '') {
  const loading = ref(false)
  const result = ref('')

  const execute = async (params, errorMsg = '生成失败') => {
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
