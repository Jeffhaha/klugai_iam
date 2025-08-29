<!--
独立IAM认证服务 - 登录表单组件
Independent IAM Authentication Service - Login Form Component
-->

<template>
  <div class="login-form">
    <div class="login-header">
      <h2 class="login-title">{{ $t('auth.login') }}</h2>
      <p class="login-subtitle">{{ $t('auth.loginSubtitle') }}</p>
    </div>

    <form @submit.prevent="handleSubmit" class="login-form-content">
      <!-- 用户名/邮箱输入 -->
      <div class="form-group">
        <label for="username" class="form-label">
          {{ $t('auth.usernameOrEmail') }}
        </label>
        <input
          id="username"
          v-model="formData.username"
          type="text"
          class="form-input"
          :class="{ 'form-input--error': errors.username }"
          :placeholder="$t('auth.usernamePlaceholder')"
          :disabled="loading"
          @blur="validateField('username')"
        />
        <div v-if="errors.username" class="form-error">
          {{ errors.username }}
        </div>
      </div>

      <!-- 密码输入 -->
      <div class="form-group">
        <label for="password" class="form-label">
          {{ $t('auth.password') }}
        </label>
        <div class="password-input-wrapper">
          <input
            id="password"
            v-model="formData.password"
            :type="showPassword ? 'text' : 'password'"
            class="form-input"
            :class="{ 'form-input--error': errors.password }"
            :placeholder="$t('auth.passwordPlaceholder')"
            :disabled="loading"
            @blur="validateField('password')"
          />
          <button
            type="button"
            class="password-toggle"
            @click="showPassword = !showPassword"
            :disabled="loading"
          >
            <svg v-if="showPassword" class="icon" viewBox="0 0 24 24">
              <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
            </svg>
            <svg v-else class="icon" viewBox="0 0 24 24">
              <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
            </svg>
          </button>
        </div>
        <div v-if="errors.password" class="form-error">
          {{ errors.password }}
        </div>
      </div>

      <!-- 记住我 -->
      <div class="form-group">
        <label class="checkbox-label">
          <input
            v-model="formData.rememberMe"
            type="checkbox"
            class="checkbox-input"
            :disabled="loading"
          />
          <span class="checkbox-custom"></span>
          {{ $t('auth.rememberMe') }}
        </label>
      </div>

      <!-- 登录按钮 -->
      <div class="form-group">
        <button
          type="submit"
          class="login-button"
          :disabled="loading || !isFormValid"
        >
          <div v-if="loading" class="loading-spinner"></div>
          {{ loading ? $t('auth.loggingIn') : $t('auth.login') }}
        </button>
      </div>

      <!-- 错误消息 -->
      <div v-if="loginError" class="login-error">
        {{ loginError }}
      </div>

      <!-- 其他操作链接 -->
      <div class="form-footer">
        <a href="#" @click.prevent="$emit('showForgotPassword')" class="link">
          {{ $t('auth.forgotPassword') }}
        </a>
        <span class="separator">•</span>
        <a href="#" @click.prevent="$emit('showRegister')" class="link">
          {{ $t('auth.createAccount') }}
        </a>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Props
const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['submit', 'showForgotPassword', 'showRegister'])

// Reactive data
const formData = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const errors = reactive({
  username: '',
  password: ''
})

const showPassword = ref(false)
const loginError = ref('')

// Computed properties
const isFormValid = computed(() => {
  return formData.username && formData.password && !errors.username && !errors.password
})

// Methods
const validateField = (field) => {
  switch (field) {
    case 'username':
      if (!formData.username) {
        errors.username = t('auth.usernameRequired')
      } else if (formData.username.length < 3) {
        errors.username = t('auth.usernameMinLength')
      } else {
        errors.username = ''
      }
      break
    case 'password':
      if (!formData.password) {
        errors.password = t('auth.passwordRequired')
      } else if (formData.password.length < 6) {
        errors.password = t('auth.passwordMinLength')
      } else {
        errors.password = ''
      }
      break
  }
}

const handleSubmit = () => {
  // Validate all fields
  validateField('username')
  validateField('password')

  if (isFormValid.value) {
    loginError.value = ''
    emit('submit', {
      username: formData.username,
      password: formData.password,
      rememberMe: formData.rememberMe
    })
  }
}

// Expose methods to parent
defineExpose({
  setError: (error) => {
    loginError.value = error
  },
  clearForm: () => {
    formData.username = ''
    formData.password = ''
    formData.rememberMe = false
    errors.username = ''
    errors.password = ''
    loginError.value = ''
  }
})
</script>

<style scoped>
.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.login-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input--error {
  border-color: #ef4444;
}

.form-input:disabled {
  background-color: #f9fafb;
  opacity: 0.6;
  cursor: not-allowed;
}

.password-input-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
}

.password-toggle:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
  fill: currentColor;
}

.form-error {
  font-size: 0.75rem;
  color: #ef4444;
  margin-top: 0.25rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

.checkbox-input {
  position: absolute;
  opacity: 0;
}

.checkbox-custom {
  width: 1rem;
  height: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 2px;
  margin-right: 0.5rem;
  position: relative;
  background: white;
}

.checkbox-input:checked + .checkbox-custom {
  background-color: #3b82f6;
  border-color: #3b82f6;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '';
  position: absolute;
  left: 3px;
  top: 0px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.login-button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-error {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.form-footer {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.875rem;
}

.link {
  color: #3b82f6;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.separator {
  margin: 0 0.5rem;
  color: #9ca3af;
}
</style>