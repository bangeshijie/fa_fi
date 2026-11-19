<template>
  <div class="login-root">
    <!-- 背景装饰层 -->
    <div class="bg-decoration"></div>

    <!-- 主登录卡片 -->
    <div class="login-card">
      <div class="brand">
        <div class="logo-icon">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="28" height="28" rx="8" fill="white" fill-opacity="0.1" />
            <path d="M10 10L16 16L22 10" stroke="white" stroke-width="2.5" stroke-linecap="round"
              stroke-linejoin="round" />
            <path d="M10 16L16 22L22 16" stroke="white" stroke-width="2.5" stroke-linecap="round"
              stroke-linejoin="round" />
            <rect x="7" y="7" width="18" height="18" rx="3" stroke="white" stroke-width="1.5" />
          </svg>
        </div>
        <h1 class="brand-title">FinPro</h1>
        <p class="brand-sub">财务管理平台 · 安全高效</p>
      </div>

      <el-form ref="loginFormRef" :model="loginForm" :rules="rules" class="login-form" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large" :prefix-icon="User" clearable />
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" size="large" :prefix-icon="Lock"
            show-password clearable />
        </el-form-item>

        <!-- 验证码区域（动态） -->
        <el-form-item v-if="captchaEnable" prop="captcha">
          <div class="captcha-wrapper">
            <el-input v-model="loginForm.captcha" placeholder="验证码" size="large" :disabled="captchaLoading"
              class="captcha-input" />
            <div class="captcha-image" @click="handleCaptcha">
              <img v-if="captchaImg" :src="captchaImg" alt="验证码" />
              <span v-else class="captcha-placeholder">
                {{ captchaLoading ? '加载中...' : '点击刷新' }}
              </span>
            </div>
          </div>
          <div v-if="captchaError" class="captcha-error">{{ captchaError }}</div>
        </el-form-item>

        <!-- 选项栏：记住我 + 忘记密码 -->
        <div class="login-options">
          <el-checkbox v-model="rememberMe" size="default" label="记住我" />
          <a href="#" class="forgot-link" @click.prevent>忘记密码？</a>
        </div>

        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>

        <div class="oauth-divider"><span>第三方登录</span></div>
        <div class="oauth-actions">
          <el-button class="oauth-btn feishu-btn" :disabled="loading" @click="handleOAuthLogin('feishu')">
            飞书登录
          </el-button>
          <el-button class="oauth-btn wechat-btn" :disabled="loading" @click="handleOAuthLogin('wechat')">
            微信登录
          </el-button>
        </div>

        <div class="register-hint">
          还没有账号？ <a href="#" @click.prevent>立即注册</a>
        </div>
      </el-form>
    </div>

    <!-- 底部备案信息 -->
    <footer class="login-footer">
      <div class="footer-content">
        <a href="#" target="_blank" class="footer-link">
          <img src="@/assets/images/gongan.png" alt="公安备案" />
          浙公网安备 33010902004606号
        </a>
        <span class="divider">|</span>
        <a href="https://beian.miit.gov.cn/" target="_blank" class="footer-link">
          浙ICP备2026020450号-1
        </a>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { useRouter, useRoute } from 'vue-router'
import { ElNotification } from 'element-plus'
import { greetings } from '@/utils'
import AuthAPI from '@/api/module_system/auth'
import { ResultEnum } from "@/enums/api/result.enum"
import { startOAuthLogin } from '@/utils/oauth'
import type { OAuthProvider } from '@/api/module_system/auth'

// --- 状态 ---
const loginFormRef = ref()
const loading = ref(false)
const captchaImg = ref('')
const captchaEnable = ref(false)
const captchaLoading = ref(false)
const captchaError = ref('')
const rememberMe = ref(false)

const authStore = useAuthStore()
const $router = useRouter()
const $route = useRoute()

const loginForm = reactive({
  username: '',
  password: '',
  captcha_key: '',
  captcha: '',
  login_type: 'PC端',
  remember: false,
})

// --- 自定义验证 ---
const validateUsername = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请输入用户名'))
    return
  }
  const trimmed = value.trim()
  const accountRegex = /^[a-zA-Z0-9][a-zA-Z0-9_.-]{3,31}$/
  if (!accountRegex.test(trimmed)) {
    callback(new Error('用户名需以字母或数字开头，4-32位，仅含字母、数字、下划线、点和横线'))
    return
  }
  callback()
}

const validatePassword = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请输入密码'))
    return
  }
  const trimmed = value.trim()
  if (trimmed.length < 6 || trimmed.length > 20) {
    callback(new Error('密码长度6-20位'))
    return
  }
  callback()
}

const rules = {
  username: [{ required: true, validator: validateUsername, trigger: 'blur' }],
  password: [{ required: true, validator: validatePassword, trigger: 'blur' }],
  captcha: [
    {
      validator: (_rule: any, value: string, callback: (error?: Error) => void) => {
        if (captchaEnable.value && !value?.trim()) {
          callback(new Error('请输入验证码'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

// --- 获取验证码 ---
const handleCaptcha = async () => {
  captchaLoading.value = true
  captchaError.value = ''
  try {
    const res = await AuthAPI.getCaptcha()
    if (res.data.code !== ResultEnum.SUCCESS) {
      throw new Error('验证码接口返回失败')
    }
    captchaEnable.value = res.data.data.enable
    if (res.data.data.enable) {
      loginForm.captcha_key = res.data.data.key
      loginForm.captcha = ''
      captchaImg.value = res.data.data.img_base
    } else {
      loginForm.captcha_key = ''
      loginForm.captcha = ''
      captchaImg.value = ''
    }
  } catch (error) {
    captchaEnable.value = true
    captchaImg.value = ''
    captchaError.value = '验证码加载失败，请检查服务后点击刷新'
    console.error('获取验证码失败', error)
  } finally {
    captchaLoading.value = false
  }
}

// --- 登录 ---
const handleLogin = async () => {
  try {
    await loginFormRef.value?.validate()
    loading.value = true
    loginForm.remember = rememberMe.value

    await authStore.login(loginForm)

    const redirect = typeof $route.query.redirect === 'string' ? $route.query.redirect : ''
    let targetPath = '/home'
    if (redirect && redirect !== '/login' && !redirect.startsWith('/login?')) {
      targetPath = redirect
    }
    await $router.replace(targetPath)

    ElNotification({
      title: `hi~ ${greetings()}`,
      message: '欢迎回来',
      type: 'success',
    })
  } catch (error) {
    handleCaptcha()
    ElNotification({
      title: '错误',
      message: error instanceof Error ? error.message : '登录失败',
      type: 'error',
    })
  } finally {
    loading.value = false
  }
}

function queryString(name: string) {
  const value = $route.query[name]
  return typeof value === 'string' ? value : ''
}

function resolveTargetPath() {
  const redirect = queryString('redirect')
  if (redirect && redirect !== '/login' && !redirect.startsWith('/login?')) return redirect
  return '/home'
}

async function clearOAuthQuery() {
  const query = { ...$route.query }
  delete query.access_token
  delete query.refresh_token
  delete query.token_type
  delete query.oauth_error
  await $router.replace({ path: '/login', query })
}

async function handleOAuthCallback() {
  const oauthError = queryString('oauth_error')
  if (oauthError) {
    await clearOAuthQuery()
    ElNotification({ title: '第三方登录失败', message: oauthError, type: 'error' })
    await handleCaptcha()
    return true
  }

  const accessToken = queryString('access_token')
  const refreshToken = queryString('refresh_token')
  if (!accessToken && !refreshToken) return false

  if (!accessToken || !refreshToken) {
    await clearOAuthQuery()
    ElNotification({ title: '第三方登录失败', message: '回调令牌不完整，请重新登录', type: 'error' })
    await handleCaptcha()
    return true
  }

  loading.value = true
  try {
    await authStore.loginWithOAuthToken({ access_token: accessToken, refresh_token: refreshToken })
    const targetPath = resolveTargetPath()
    await $router.replace(targetPath)
    ElNotification({ title: `hi~ ${greetings()}`, message: '第三方登录成功', type: 'success' })
  } catch (error) {
    await clearOAuthQuery()
    ElNotification({ title: '第三方登录失败', message: error instanceof Error ? error.message : '登录初始化失败', type: 'error' })
    await handleCaptcha()
  } finally {
    loading.value = false
  }
  return true
}

function handleOAuthLogin(provider: OAuthProvider) {
  const redirect = queryString('redirect')
  startOAuthLogin(provider, redirect)
}

onMounted(async () => {
  const handled = await handleOAuthCallback()
  if (!handled) await handleCaptcha()
})
</script>

<style scoped lang="scss">
.login-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;

  /* 背景图优化 - 使用 image-set 支持不同分辨率 */
  background-image: url('@/assets/images/background.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;

  /* 使用 CSS 渲染优化，提升图片清晰度 */
  image-rendering: auto;
  image-rendering: -webkit-optimize-contrast;

  /* 背景遮罩层 - 减弱遮罩透明度让背景更清晰 */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(11, 17, 32, 0.5);
    z-index: 0;
    /* 移除 blur 滤镜，避免影响背景清晰度 */
  }
}

/* 背景装饰层 - 保留但无实际内容 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

/* 登录卡片 —— 毛玻璃效果 */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-radius: 48px;
  padding: 40px 32px 36px;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: transform 0.3s ease;

  /* 登录卡片内部背景图片 */
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 48px;
    background-image: url('@/assets/images/login_form.png');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0.01;
    pointer-events: none;
    z-index: -1;
  }

  &:hover {
    transform: translateY(-4px);
  }
}

.brand {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.logo-icon {
  display: inline-flex;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #4f7cff, #7c3aed);
  border-radius: 20px;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  box-shadow: 0 12px 24px rgba(79, 124, 255, 0.3);

  svg {
    width: 32px;
    height: 32px;
  }
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.5px;
  margin: 0 0 4px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.brand-sub {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.3px;
  margin: 0;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
}

/* 表单 - 调整输入框文字颜色为黑色 */
.login-form {
  position: relative;
  z-index: 1;

  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    box-shadow: none;
    transition: all 0.2s;
    padding: 4px 16px;

    &:hover {
      border-color: rgba(255, 255, 255, 0.4);
      background: rgba(255, 255, 255, 0.95);
    }

    &.is-focus {
      border-color: #4f7cff;
      box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.2);
      background: #ffffff;
    }

    .el-input__prefix {
      color: #6b7280;
      margin-right: 8px;
    }

    .el-input__inner {
      color: #1a1a1a;
      font-size: 15px;
      font-weight: 500;

      &::placeholder {
        color: #9ca3af;
        font-weight: 400;
      }
    }

    .el-input__suffix {
      .el-input__suffix-inner {
        .el-icon {
          color: #6b7280;
          font-size: 18px;
        }

        .el-icon-view,
        .el-icon-hide {
          color: #6b7280;

          &:hover {
            color: #1a1a1a;
          }
        }
      }
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 18px;

    .el-form-item__error {
      color: #ffb3b3;
      font-size: 12px;
      padding-top: 4px;
      text-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    }
  }
}

/* 验证码 - 输入框黑色文字 */
.captcha-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;

  .captcha-input {
    flex: 1;

    :deep(.el-input__wrapper) {
      background: rgba(255, 255, 255, 0.92);

      .el-input__inner {
        color: #1a1a1a;
        font-weight: 500;

        &::placeholder {
          color: #9ca3af;
          font-weight: 400;
        }
      }
    }
  }

  .captcha-image {
    flex-shrink: 0;
    width: 110px;
    height: 44px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;

    &:hover {
      border-color: rgba(255, 255, 255, 0.25);
      background: rgba(255, 255, 255, 0.08);
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }

    .captcha-placeholder {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.35);
      user-select: none;
    }
  }
}

.captcha-error {
  margin-top: 6px;
  color: #ffb3b3;
  font-size: 12px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* 选项 */
.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0 24px;

  :deep(.el-checkbox) {
    color: rgba(255, 255, 255, 0.85);

    .el-checkbox__label {
      color: rgba(255, 255, 255, 0.85);
      font-size: 14px;
      text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
    }

    .el-checkbox__inner {
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(255, 255, 255, 0.15);
      width: 18px;
      height: 18px;
      border-radius: 6px;

      &::after {
        border-color: #fff;
      }
    }

    &.is-checked .el-checkbox__inner {
      background: #4f7cff;
      border-color: #4f7cff;
    }
  }

  .forgot-link {
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    text-decoration: none;
    transition: color 0.2s;
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);

    &:hover {
      color: #fff;
    }
  }
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, #4f7cff, #7c3aed);
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 8px 24px rgba(79, 124, 255, 0.3);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(79, 124, 255, 0.4);
    background: linear-gradient(135deg, #5a87ff, #8b4fff);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 4px 12px rgba(79, 124, 255, 0.3);
  }

  &.is-loading {
    opacity: 0.8;
  }
}

.register-hint {
  text-align: center;
  margin-top: 18px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);

  a {
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;

    &:hover {
      color: #fff;
    }
  }
}

/* 底部备案 */
.login-footer {
  position: relative;
  z-index: 2;
  margin-top: 32px;
  width: 100%;
  max-width: 420px;
  text-align: center;

  .footer-content {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.3);
    flex-wrap: wrap;

    .footer-link {
      color: inherit;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: color 0.2s;

      img {
        width: 16px;
        height: 16px;
        display: inline-block;
        vertical-align: middle;
        filter: grayscale(0.5) brightness(1.8);
      }

      &:hover {
        color: rgba(255, 255, 255, 0.6);
      }
    }

    .divider {
      opacity: 0.3;
    }
  }
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    padding: 28px 20px 24px;
    border-radius: 32px;
  }

  .brand-title {
    font-size: 24px;
  }

  .captcha-wrapper .captcha-image {
    width: 90px;
    height: 40px;
  }

  .login-btn {
    height: 48px;
    font-size: 15px;
  }
}

/* 高清屏优化 - 如果使用 2x 图片 */
@media (-webkit-min-device-pixel-ratio: 2),
(min-resolution: 192dpi) {
  .login-root { background-image: url('@/assets/images/background.jpg'); }
}

.oauth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 6px 0 14px;
  color: rgba(255, 255, 255, 0.38);
  font-size: 12px;

  &::before,
  &::after {
    content: '';
    height: 1px;
    flex: 1;
    background: rgba(255, 255, 255, 0.16);
  }
}

.oauth-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.oauth-btn {
  height: 40px;
  margin-left: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.86);
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;

  &:hover {
    transform: translateY(-1px);
    color: #fff;
    border-color: rgba(255, 255, 255, 0.42);
    background: rgba(255, 255, 255, 0.14);
  }
}

.feishu-btn:hover { border-color: #4c9aff; }
.wechat-btn:hover { border-color: #36c95f; }
</style>
