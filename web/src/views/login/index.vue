<template>
  <AppPage :show-footer="false">
    <div class="hm-login-page">
      <div class="hm-login-card">
        <div class="hm-login-brand">
          <div class="brand-icon">
            <icon-custom-logo text-40 />
          </div>
          <h1 class="brand-title">{{ $t('app_name') }}</h1>
          <p class="brand-subtitle">AI Agent 智能助手平台</p>
        </div>

        <template v-if="!isRegister">
          <div class="hm-form-group">
            <n-input
              v-model:value="loginInfo.username"
              autofocus
              class="hm-input"
              placeholder="请输入用户名"
              :maxlength="20"
            >
              <template #prefix>
                <TheIcon icon="icon-park-outline:user" :size="18" color="var(--hm-font-tertiary)" />
              </template>
            </n-input>
          </div>
          <div class="hm-form-group">
            <n-input
              v-model:value="loginInfo.password"
              class="hm-input"
              type="password"
              show-password-on="mousedown"
              placeholder="请输入密码"
              :maxlength="20"
              @keypress.enter="handleLogin"
            >
              <template #prefix>
                <TheIcon icon="icon-park-outline:lock" :size="18" color="var(--hm-font-tertiary)" />
              </template>
            </n-input>
          </div>
          <div class="hm-captcha-group">
            <SliderCaptcha
              v-if="captchaData"
              :bg="captchaData.bg_image"
              :slider="captchaData.slider_image"
              :y="captchaData.y_offset"
              @success="onCaptchaSuccess"
              @fail="onCaptchaFail"
              @refresh="refreshCaptcha"
            />
          </div>
          <n-button
            class="hm-btn-primary"
            :loading="loading"
            @click="handleLogin"
          >
            {{ $t('views.login.text_login') }}
          </n-button>
          <div class="hm-switch-link">
            <span @click="switchToRegister">还没有账号？<em>立即注册</em></span>
          </div>
        </template>

        <template v-else>
          <div class="hm-form-group">
            <n-input
              v-model:value="registerInfo.username"
              autofocus
              class="hm-input"
              placeholder="请输入用户名"
              :maxlength="20"
            >
              <template #prefix>
                <TheIcon icon="icon-park-outline:user" :size="18" color="var(--hm-font-tertiary)" />
              </template>
            </n-input>
          </div>
          <div class="hm-form-group">
            <n-input
              v-model:value="registerInfo.email"
              class="hm-input"
              placeholder="请输入邮箱"
              :maxlength="50"
            >
              <template #prefix>
                <TheIcon icon="icon-park-outline:mail" :size="18" color="var(--hm-font-tertiary)" />
              </template>
            </n-input>
          </div>
          <div class="hm-form-group">
            <n-input
              v-model:value="registerInfo.password"
              class="hm-input"
              type="password"
              show-password-on="mousedown"
              placeholder="请输入密码"
              :maxlength="20"
            >
              <template #prefix>
                <TheIcon icon="icon-park-outline:lock" :size="18" color="var(--hm-font-tertiary)" />
              </template>
            </n-input>
          </div>
          <div class="hm-form-group">
            <n-input
              v-model:value="registerInfo.confirmPassword"
              class="hm-input"
              type="password"
              show-password-on="mousedown"
              placeholder="请确认密码"
              :maxlength="20"
              @keypress.enter="handleRegister"
            >
              <template #prefix>
                <TheIcon icon="icon-park-outline:lock" :size="18" color="var(--hm-font-tertiary)" />
              </template>
            </n-input>
          </div>
          <n-button
            class="hm-btn-primary"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </n-button>
          <div class="hm-switch-link">
            <span @click="switchToLogin">已有账号？<em>返回登录</em></span>
          </div>
        </template>
      </div>
    </div>
  </AppPage>
</template>

<script setup>
import { lStorage, setToken, setRefreshToken } from '@/utils'
import api from '@/api'
import { addDynamicRoutes } from '@/router'
import { useI18n } from 'vue-i18n'
import TheIcon from '@/components/icon/TheIcon.vue'
import SliderCaptcha from '@/components/SliderCaptcha.vue'

const router = useRouter()
const { query } = useRoute()
const { t } = useI18n({ useScope: 'global' })

const isRegister = ref(false)
const loading = ref(false)

const loginInfo = ref({
  username: '',
  password: '',
})

const registerInfo = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const captchaData = ref(null)
const captchaVerified = ref(false)
const captchaToken = ref({ captcha_id: '', x: 0 })

initLoginInfo()
fetchCaptcha()

function initLoginInfo() {
  const localLoginInfo = lStorage.get('loginInfo')
  if (localLoginInfo) {
    loginInfo.value.username = localLoginInfo.username || ''
  }
}

async function fetchCaptcha() {
  try {
    const res = await api.getCaptcha()
    captchaData.value = res.data
    captchaVerified.value = false
    captchaToken.value = { captcha_id: '', x: 0 }
  } catch (e) {
    console.error('fetch captcha error', e)
  }
}

function onCaptchaSuccess({ x }) {
  captchaVerified.value = true
  captchaToken.value = { captcha_id: captchaData.value.captcha_id, x }
}

function onCaptchaFail() {
  captchaVerified.value = false
  $message.warning('验证码校验失败，请重试')
}

function refreshCaptcha() {
  fetchCaptcha()
}

function switchToRegister() {
  isRegister.value = true
  registerInfo.value = { username: '', email: '', password: '', confirmPassword: '' }
}

function switchToLogin() {
  isRegister.value = false
  fetchCaptcha()
}

async function handleLogin() {
  const { username, password } = loginInfo.value
  if (!username || !password) {
    $message.warning(t('views.login.message_input_username_password'))
    return
  }
  if (!captchaVerified.value) {
    $message.warning('请完成滑块验证')
    return
  }
  try {
    loading.value = true
    $message.loading(t('views.login.message_verifying'))
    const res = await api.login({
      username,
      password: password.toString(),
      captcha_id: captchaToken.value.captcha_id,
      x: captchaToken.value.x,
    })
    $message.success(t('views.login.message_login_success'))
    setToken(res.data.access_token)
    setRefreshToken(res.data.refresh_token)
    await addDynamicRoutes()
    if (query.redirect) {
      const path = query.redirect
      Reflect.deleteProperty(query, 'redirect')
      router.push({ path, query })
    } else {
      router.push('/')
    }
  } catch (e) {
    console.error('login error', e.error)
    refreshCaptcha()
  }
  loading.value = false
}

async function handleRegister() {
  const { username, email, password, confirmPassword } = registerInfo.value
  if (!username) { $message.warning('请输入用户名'); return }
  if (!email) { $message.warning('请输入邮箱'); return }
  if (!password) { $message.warning('请输入密码'); return }
  if (password !== confirmPassword) { $message.warning('两次密码输入不一致'); return }
  try {
    loading.value = true
    await api.register({ username, email, password })
    $message.success('注册成功，请登录')
    loginInfo.value.username = username
    loginInfo.value.password = ''
    switchToLogin()
  } catch (e) {
    console.error('register error', e)
  }
  loading.value = false
}
</script>

<style scoped>
.hm-login-page {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--hm-bg-primary);
  position: relative;
  overflow: hidden;
}

.hm-login-page::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -20%;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(10, 89, 247, 0.06) 0%, transparent 70%);
  pointer-events: none;
}

.hm-login-card {
  width: 400px;
  background: var(--hm-bg-glass);
  backdrop-filter: var(--hm-blur-glass-strong);
  -webkit-backdrop-filter: var(--hm-blur-glass-strong);
  border-radius: var(--hm-radius-xl);
  border: 1px solid var(--hm-border-glass);
  padding: 48px 36px 36px;
  box-shadow: var(--hm-shadow-layered), 0 12px 40px rgba(10, 89, 247, 0.08);
  position: relative;
  z-index: 1;
}

.hm-login-brand {
  text-align: center;
  margin-bottom: 36px;
}

.brand-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--hm-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: var(--hm-shadow-brand);
  transition: transform 0.35s var(--hm-spring);
}

.brand-icon:hover {
  transform: scale(1.08) rotate(-3deg);
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--hm-font-primary);
  margin-bottom: 6px;
  letter-spacing: -0.3px;
}

.brand-subtitle {
  font-size: 14px;
  color: var(--hm-font-tertiary);
}

.hm-form-group {
  margin-bottom: 16px;
}

.hm-captcha-group {
  margin-bottom: 16px;
  display: flex;
  justify-content: center;
}

.hm-input {
  height: 44px;
  border-radius: var(--hm-radius-lg);
  font-size: 14px;
  transition: all 0.3s var(--hm-spring);
}

.hm-btn-primary {
  width: 100%;
  height: 44px;
  border-radius: var(--hm-radius-lg);
  font-size: 16px;
  font-weight: 500;
  margin-top: 8px;
  background: linear-gradient(135deg, #0A59F7 0%, #337BF7 100%) !important;
  box-shadow: var(--hm-shadow-brand);
  transition: all 0.3s var(--hm-spring);
}

.hm-btn-primary:hover {
  box-shadow: 0 6px 20px rgba(10, 89, 247, 0.35) !important;
  transform: translateY(-2px);
}

.hm-btn-primary:active {
  transform: translateY(0) scale(0.98);
  transition-duration: 0.1s;
}

.hm-switch-link {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: var(--hm-font-tertiary);
  cursor: pointer;
  transition: all 0.25s var(--hm-spring);
}

.hm-switch-link em {
  font-style: normal;
  color: var(--hm-brand);
}

.hm-switch-link:hover em {
  text-decoration: underline;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .hm-login-card {
    width: calc(100% - 32px);
    max-width: 400px;
    padding: 36px 24px 28px;
  }
  .brand-title {
    font-size: 24px;
  }
  .brand-icon {
    width: 52px;
    height: 52px;
  }
  .hm-login-page::before {
    width: 300px;
    height: 300px;
  }
}

@media (max-width: 480px) {
  .hm-login-card {
    padding: 28px 18px 22px;
  }
  .brand-title {
    font-size: 22px;
  }
  .hm-input {
    height: 40px;
  }
  .hm-btn-primary {
    height: 40px;
    font-size: 15px;
  }
}
</style>
