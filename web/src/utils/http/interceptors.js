import {
  getToken,
  getRefreshToken,
  setToken,
  setRefreshToken,
  removeToken,
  removeRefreshToken,
} from '@/utils/auth/token'
import { resolveResError } from './helpers'
import { useUserStore } from '@/store'
import { t } from '@/utils/common/i18nHelper'

let isRefreshing = false
let pendingRequests = []

function onRefreshed(newToken) {
  pendingRequests.forEach((cb) => cb(newToken))
  pendingRequests = []
}

function onRefreshFailed() {
  pendingRequests.forEach((cb) => cb(null))
  pendingRequests = []
}

export function reqResolve(config) {
  if (config.noNeedToken) {
    return config
  }

  const token = getToken()
  if (token) {
    config.headers.token = config.headers.token || token
  }

  return config
}

export function reqReject(error) {
  return Promise.reject(error)
}

export function resResolve(response) {
  const { data, status, statusText } = response
  if (data?.code !== 200) {
    const code = data?.code ?? status
    const message = resolveResError(code, data?.msg ?? statusText)
    window.$message?.error(message, { keepAliveOnHover: true })
    return Promise.reject({ code, message, error: data || response })
  }
  return Promise.resolve(data)
}

export async function resReject(error) {
  if (!error || !error.response) {
    const code = error?.code
    const message = resolveResError(code, error.message)
    window.$message?.error(message)
    return Promise.reject({ code, message, error })
  }
  const { data, status } = error.response
  const originalRequest = error.config

  if (status === 401 && !originalRequest._retry) {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      forceLogout()
      return Promise.reject({ code: 401, message: t('common.http.unauthorized'), error })
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingRequests.push((newToken) => {
          if (newToken) {
            originalRequest.headers.token = newToken
            import('axios')
              .then(({ default: axios }) => axios(originalRequest))
              .then(resolve, reject)
          } else {
            forceLogout()
            reject({ code: 401, message: t('common.http.unauthorized'), error })
          }
        })
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const axios = (await import('axios')).default
      const baseURL = originalRequest.baseURL || import.meta.env.VITE_BASE_API
      const res = await axios.post(`${baseURL}/base/refresh_token`, { refresh_token: refreshToken })
      const { access_token, refresh_token: newRefreshToken } = res.data?.data || {}
      if (!access_token) {
        throw new Error(t('common.http.refresh_token_empty'))
      }
      setToken(access_token)
      setRefreshToken(newRefreshToken || refreshToken)

      onRefreshed(access_token)
      isRefreshing = false

      originalRequest.headers.token = access_token
      return axios(originalRequest)
    } catch (refreshError) {
      onRefreshFailed()
      isRefreshing = false
      forceLogout()
      return Promise.reject({ code: 401, message: t('common.http.unauthorized'), error: refreshError })
    }
  }

  const code = data?.code ?? status
  const message = resolveResError(code, data?.msg ?? error.message)
  window.$message?.error(message, { keepAliveOnHover: true })
  return Promise.reject({ code, message, error: error.response?.data || error.response })
}

function forceLogout() {
  try {
    const userStore = useUserStore()
    userStore.logout()
  } catch {
    removeToken()
    removeRefreshToken()
    window.location.href = '/login'
  }
}
