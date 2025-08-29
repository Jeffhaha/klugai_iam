<!--
独立IAM认证服务 - 登录页面
Independent IAM Authentication Service - Login Page
-->

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo">
            <svg class="logo-icon" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h1 class="brand-title">{{ $t('auth.brandTitle') }}</h1>
          <p class="brand-description">{{ $t('auth.brandDescription') }}</p>
          
          <div class="features-list">
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 24 24">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>{{ $t('auth.feature.secure') }}</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 24 24">
                <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              <span>{{ $t('auth.feature.fast') }}</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 24 24">
                <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
              <span>{{ $t('auth.feature.reliable') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧表单区域 -->
      <div class="form-section">
        <div class="form-container">
          <!-- 语言切换器 -->
          <div class="language-switcher">
            <select v-model="currentLocale" @change="changeLocale" class="language-select">
              <option value="en">English</option>
              <option value="zh-CN">中文</option>
            </select>
          </div>

          <!-- 表单切换器 -->
          <div class="form-tabs">
            <button
              class="form-tab"
              :class="{ 'form-tab--active': currentForm === 'login' }"
              @click="switchForm('login')"
            >
              {{ $t('auth.login') }}
            </button>
            <button
              class="form-tab"
              :class="{ 'form-tab--active': currentForm === 'register' }"
              @click="switchForm('register')"
            >
              {{ $t('auth.register') }}
            </button>
          </div>

          <!-- 登录表单 -->
          <LoginForm
            v-if="currentForm === 'login'"
            ref="loginFormRef"
            :loading="authLoading"
            @submit="handleLogin"
            @show-forgot-password="switchForm('forgot-password')"
            @show-register="switchForm('register')"
          />

          <!-- 注册表单 -->
          <RegisterForm
            v-if="currentForm === 'register'"
            ref="registerFormRef"
            :loading="authLoading"
            @submit="handleRegister"
            @show-login="switchForm('login')"
            @show-terms="showTermsModal = true"
          />

          <!-- 忘记密码表单 -->
          <ForgotPasswordForm
            v-if="currentForm === 'forgot-password'"
            ref="forgotPasswordFormRef"
            :loading="authLoading"
            @submit="handleForgotPassword"
            @show-login="switchForm('login')"
          />
        </div>
      </div>
    </div>

    <!-- 条款模态框 -->
    <TermsModal
      v-if="showTermsModal"
      @close="showTermsModal = false"
      @accept="handleAcceptTerms"
    />

    <!-- 成功消息 -->
    <Notification
      v-if="notification.show"
      :type="notification.type"
      :message="notification.message"
      @close="hideNotification"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

import LoginForm from '@/components/Auth/LoginForm.vue'
import RegisterForm from '@/components/Auth/RegisterForm.vue'
import ForgotPasswordForm from '@/components/Auth/ForgotPasswordForm.vue'
import TermsModal from '@/components/Auth/TermsModal.vue'
import Notification from '@/components/Common/Notification.vue'

const { t, locale } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

// Reactive data
const currentForm = ref('login')
const authLoading = ref(false)
const showTermsModal = ref(false)
const currentLocale = ref(locale.value)

const notification = reactive({
  show: false,
  type: 'success',
  message: ''
})

// Form refs
const loginFormRef = ref(null)
const registerFormRef = ref(null)
const forgotPasswordFormRef = ref(null)

// Methods
const switchForm = (form) => {
  currentForm.value = form
  hideNotification()
}

const changeLocale = () => {
  locale.value = currentLocale.value
  localStorage.setItem('locale', currentLocale.value)
}

const showNotification = (type, message) => {
  notification.type = type
  notification.message = message
  notification.show = true
  
  // Auto hide after 5 seconds
  setTimeout(() => {
    hideNotification()
  }, 5000)
}

const hideNotification = () => {
  notification.show = false
}

const handleLogin = async (loginData) => {
  try {
    authLoading.value = true
    
    const result = await authStore.login(loginData)
    
    if (result.success) {
      showNotification('success', t('auth.loginSuccess'))
      
      // Redirect to dashboard or intended route
      const redirect = router.currentRoute.value.query.redirect || '/dashboard'
      setTimeout(() => {
        router.push(redirect)
      }, 1500)
    } else {
      loginFormRef.value?.setError(result.message || t('auth.loginFailed'))
    }
  } catch (error) {
    console.error('Login error:', error)
    loginFormRef.value?.setError(t('auth.loginError'))
  } finally {
    authLoading.value = false
  }
}

const handleRegister = async (registerData) => {
  try {
    authLoading.value = true
    
    const result = await authStore.register(registerData)
    
    if (result.success) {
      showNotification('success', t('auth.registerSuccess'))
      registerFormRef.value?.clearForm()
      
      // Switch to login form after successful registration
      setTimeout(() => {
        switchForm('login')
      }, 2000)
    } else {
      registerFormRef.value?.setError(result.message || t('auth.registerFailed'))
    }
  } catch (error) {
    console.error('Register error:', error)
    registerFormRef.value?.setError(t('auth.registerError'))
  } finally {
    authLoading.value = false
  }
}

const handleForgotPassword = async (forgotPasswordData) => {
  try {
    authLoading.value = true
    
    const result = await authStore.forgotPassword(forgotPasswordData)
    
    if (result.success) {
      showNotification('success', t('auth.forgotPasswordSuccess'))
      forgotPasswordFormRef.value?.clearForm()
      
      // Switch to login form
      setTimeout(() => {
        switchForm('login')
      }, 2000)
    } else {
      forgotPasswordFormRef.value?.setError(result.message || t('auth.forgotPasswordFailed'))
    }
  } catch (error) {
    console.error('Forgot password error:', error)
    forgotPasswordFormRef.value?.setError(t('auth.forgotPasswordError'))
  } finally {
    authLoading.value = false
  }
}

const handleAcceptTerms = () => {
  showTermsModal.value = false
  showNotification('info', t('auth.termsAccepted'))
}

// Lifecycle
onMounted(() => {
  // Load saved locale
  const savedLocale = localStorage.getItem('locale')
  if (savedLocale) {
    currentLocale.value = savedLocale
    locale.value = savedLocale
  }
  
  // Check if user is already logged in
  if (authStore.isLoggedIn) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.login-container {
  display: flex;
  max-width: 1000px;
  width: 100%;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  padding: 3rem;
  display: flex;
  align-items: center;
  min-height: 600px;
}

.brand-content {
  max-width: 400px;
}

.brand-logo {
  margin-bottom: 2rem;
}

.logo-icon {
  width: 3rem;
  height: 3rem;
  fill: currentColor;
}

.brand-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  line-height: 1.2;
}

.brand-description {
  font-size: 1.125rem;
  opacity: 0.9;
  margin-bottom: 3rem;
  line-height: 1.6;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.feature-icon {
  width: 1.5rem;
  height: 1.5rem;
  fill: currentColor;
  opacity: 0.8;
}

.form-section {
  flex: 1;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 600px;
}

.form-container {
  width: 100%;
  max-width: 450px;
  padding: 2rem;
  position: relative;
}

.language-switcher {
  position: absolute;
  top: 1rem;
  right: 1rem;
}

.language-select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
}

.form-tabs {
  display: flex;
  margin-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.form-tab {
  flex: 1;
  padding: 1rem;
  background: none;
  border: none;
  font-size: 1rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
  border-bottom: 2px solid transparent;
}

.form-tab--active {
  color: #4f46e5;
  border-bottom-color: #4f46e5;
}

.form-tab:hover {
  color: #4f46e5;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    max-width: 500px;
  }
  
  .brand-section {
    padding: 2rem;
    min-height: auto;
  }
  
  .brand-title {
    font-size: 1.5rem;
  }
  
  .brand-description {
    font-size: 1rem;
    margin-bottom: 2rem;
  }
  
  .features-list {
    gap: 1rem;
  }
  
  .form-container {
    padding: 1.5rem;
  }
}

@media (max-width: 480px) {
  .login-page {
    padding: 0.5rem;
  }
  
  .brand-section {
    padding: 1.5rem;
  }
  
  .form-container {
    padding: 1rem;
  }
}
</style>