import { useUserStore } from '@/store'

let _t = null
function t(key, params) {
  if (!_t) {
    // Lazy: i18n is fully initialized by first function call
    const mod = window.__i18n_module__
    _t = mod?.default?.global?.t ?? ((k) => k)
  }
  return _t(key, params)
}

export function addBaseParams(params) {
  if (!params.userId) {
    params.userId = useUserStore().userId
  }
}

export function resolveResError(code, message) {
  switch (code) {
    case 400:
      message = message ?? t('common.http.bad_request')
      break
    case 401:
      message = message ?? t('common.http.unauthorized')
      break
    case 403:
      message = message ?? t('common.http.forbidden')
      break
    case 404:
      message = message ?? t('common.http.not_found')
      break
    case 500:
      message = message ?? t('common.http.server_error')
      break
    default:
      message = message ?? t('common.http.unknown_error', { code })
      break
  }
  return message
}
