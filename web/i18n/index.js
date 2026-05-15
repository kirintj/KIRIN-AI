import { createI18n } from 'vue-i18n'
import { lStorage } from '@/utils'

import messages from './messages'

const currentLocale = lStorage.get('locale')

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: currentLocale || 'cn',
  fallbackLocale: 'cn',
  messages: messages,
})

// Register globally for lazy access in utils (avoids circular dependency)
if (typeof window !== 'undefined') {
  window.__kirin_i18n__ = i18n
}

export default i18n
