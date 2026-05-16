import { useUserStore } from '@/store'
import { t } from '@/utils/common/i18nHelper'

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
