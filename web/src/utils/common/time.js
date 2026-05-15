  import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import i18n from '~/i18n'

const t = i18n.global.t

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

export function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return t('common.time.just_now')
  if (diffMins < 60) return t('common.time.minutes_ago', { n: diffMins })
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return t('common.time.hours_ago', { n: diffHours })
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return t('common.time.days_ago', { n: diffDays })
  const locale = i18n.global.locale === 'cn' ? 'zh-CN' : 'en-US'
  return date.toLocaleDateString(locale, { month: 'short', day: 'numeric' })
}

export function formatMsgTime(dateStr) {
  if (!dateStr) return ''
  const locale = i18n.global.locale === 'cn' ? 'zh-CN' : 'en-US'
  return new Date(dateStr).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' })
}

export function shouldShowTimeDivider(messages, index) {
  if (index === 0) return true
  const curr = messages[index].timestamp
  const prev = messages[index - 1].timestamp
  if (!curr || !prev) return false
  return new Date(curr).getTime() - new Date(prev).getTime() > 5 * 60 * 1000
}

export function formatShortDate(dateStr) {
  if (!dateStr) return ''
  const locale = i18n.global.locale === 'cn' ? 'zh-CN' : 'en-US'
  return new Date(dateStr).toLocaleDateString(locale, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function formatDateTimeShort(dateStr) {
  if (!dateStr) return ''
  const locale = i18n.global.locale === 'cn' ? 'zh-CN' : 'en-US'
  return new Date(dateStr).toLocaleString(locale, { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export function formatDueDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const hasTime = dateStr.includes(':') || dateStr.includes('T')
  const locale = i18n.global.locale === 'cn' ? 'zh-CN' : 'en-US'
  if (hasTime) {
    return d.toLocaleString(locale, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }
  return d.toLocaleDateString(locale, { month: 'short', day: 'numeric' })
}
