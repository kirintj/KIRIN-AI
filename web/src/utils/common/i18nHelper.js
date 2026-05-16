let _t = null

export function t(key, params) {
  if (!_t) {
    const i18n = window.__kirin_i18n__
    _t = i18n?.global?.t ?? ((k) => k)
  }
  return _t(key, params)
}
