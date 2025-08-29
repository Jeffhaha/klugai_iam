<!--
独立IAM认证服务 - 注册表单组件
Independent IAM Authentication Service - Register Form Component
-->

<template>
  <div class="register-form">
    <div class="register-header">
      <h2 class="register-title">{{ $t('auth.createAccount') }}</h2>
      <p class="register-subtitle">{{ $t('auth.createAccountSubtitle') }}</p>
    </div>

    <form @submit.prevent="handleSubmit" class="register-form-content">
      <!-- 用户名输入 -->
      <div class="form-group">
        <label for="username" class="form-label">
          {{ $t('auth.username') }}
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

      <!-- 邮箱输入 -->
      <div class="form-group">
        <label for="email" class="form-label">
          {{ $t('auth.email') }}
        </label>
        <input
          id="email"
          v-model="formData.email"
          type="email"
          class="form-input"
          :class="{ 'form-input--error': errors.email }"
          :placeholder="$t('auth.emailPlaceholder')"
          :disabled="loading"
          @blur="validateField('email')"
        />
        <div v-if="errors.email" class="form-error">
          {{ errors.email }}
        </div>
      </div>

      <!-- 姓名输入 -->
      <div class="form-row">
        <div class="form-group form-group--half">
          <label for="firstName" class="form-label">
            {{ $t('auth.firstName') }}
          </label>
          <input
            id="firstName"
            v-model="formData.firstName"
            type="text"
            class="form-input"
            :class="{ 'form-input--error': errors.firstName }"
            :placeholder="$t('auth.firstNamePlaceholder')"
            :disabled="loading"
            @blur="validateField('firstName')"
          />
          <div v-if="errors.firstName" class="form-error">
            {{ errors.firstName }}
          </div>
        </div>

        <div class="form-group form-group--half">
          <label for="lastName" class="form-label">
            {{ $t('auth.lastName') }}
          </label>
          <input
            id="lastName"
            v-model="formData.lastName"
            type="text"
            class="form-input"
            :class="{ 'form-input--error': errors.lastName }"
            :placeholder="$t('auth.lastNamePlaceholder')"
            :disabled="loading"
            @blur="validateField('lastName')"
          />
          <div v-if="errors.lastName" class="form-error">
            {{ errors.lastName }}
          </div>
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
        <div class="password-strength">
          <div class="strength-indicator" :class="passwordStrength.class">
            <div v-for="i in 4" :key="i" class="strength-bar"></div>
          </div>
          <span class="strength-text">{{ passwordStrength.text }}</span>
        </div>
      </div>

      <!-- 确认密码输入 -->
      <div class="form-group">
        <label for="confirmPassword" class="form-label">
          {{ $t('auth.confirmPassword') }}
        </label>
        <div class="password-input-wrapper">
          <input
            id="confirmPassword"
            v-model="formData.confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            class="form-input"
            :class="{ 'form-input--error': errors.confirmPassword }"
            :placeholder="$t('auth.confirmPasswordPlaceholder')"
            :disabled="loading"
            @blur="validateField('confirmPassword')"
          />
          <button
            type="button"
            class="password-toggle"
            @click="showConfirmPassword = !showConfirmPassword"
            :disabled="loading"
          >
            <svg v-if="showConfirmPassword" class="icon" viewBox="0 0 24 24">
              <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
            </svg>
            <svg v-else class="icon" viewBox="0 0 24 24">
              <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
            </svg>
          </button>
        </div>
        <div v-if="errors.confirmPassword" class="form-error">
          {{ errors.confirmPassword }}
        </div>
      </div>

      <!-- 同意条款 -->
      <div class="form-group">
        <label class="checkbox-label">
          <input
            v-model="formData.agreeTerms"
            type="checkbox"
            class="checkbox-input"
            :disabled="loading"
          />
          <span class="checkbox-custom"></span>
          {{ $t('auth.agreeTerms') }}
          <a href="#" @click.prevent="$emit('showTerms')" class="link">
            {{ $t('auth.termsOfService') }}
          </a>
        </label>
        <div v-if="errors.agreeTerms" class="form-error">
          {{ errors.agreeTerms }}
        </div>
      </div>

      <!-- 注册按钮 -->
      <div class="form-group">
        <button
          type="submit"
          class="register-button"
          :disabled="loading || !isFormValid"
        >
          <div v-if="loading" class="loading-spinner"></div>
          {{ loading ? $t('auth.registering') : $t('auth.createAccount') }}
        </button>
      </div>

      <!-- 错误消息 -->
      <div v-if="registerError" class="register-error">
        {{ registerError }}
      </div>

      <!-- 其他操作链接 -->
      <div class="form-footer">
        {{ $t('auth.alreadyHaveAccount') }}
        <a href="#" @click.prevent="$emit('showLogin')" class="link">
          {{ $t('auth.login') }}
        </a>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
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
const emit = defineEmits(['submit', 'showLogin', 'showTerms'])

// Reactive data
const formData = reactive({
  username: '',
  email: '',
  firstName: '',
  lastName: '',
  password: '',
  confirmPassword: '',
  agreeTerms: false
})

const errors = reactive({
  username: '',
  email: '',
  firstName: '',
  lastName: '',
  password: '',
  confirmPassword: '',
  agreeTerms: ''
})

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const registerError = ref('')

// Password strength calculation
const passwordStrength = computed(() => {
  const password = formData.password
  if (!password) {
    return { class: 'strength-none', text: t('auth.passwordStrength.none') }
  }

  let score = 0
  
  // Length check
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  
  // Character type checks
  if (/[a-z]/.test(password)) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score >= 5) {
    return { class: 'strength-strong', text: t('auth.passwordStrength.strong') }
  } else if (score >= 3) {
    return { class: 'strength-medium', text: t('auth.passwordStrength.medium') }
  } else if (score >= 1) {
    return { class: 'strength-weak', text: t('auth.passwordStrength.weak') }
  } else {
    return { class: 'strength-none', text: t('auth.passwordStrength.none') }
  }
})

// Computed properties
const isFormValid = computed(() => {
  return (
    formData.username &&
    formData.email &&
    formData.firstName &&
    formData.lastName &&
    formData.password &&
    formData.confirmPassword &&
    formData.agreeTerms &&
    !Object.values(errors).some(error => error)
  )
})

// Methods
const validateField = (field) => {
  switch (field) {
    case 'username':
      if (!formData.username) {
        errors.username = t('auth.usernameRequired')
      } else if (formData.username.length < 3) {
        errors.username = t('auth.usernameMinLength')
      } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
        errors.username = t('auth.usernameInvalid')
      } else {
        errors.username = ''
      }
      break
    case 'email':
      if (!formData.email) {
        errors.email = t('auth.emailRequired')
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        errors.email = t('auth.emailInvalid')
      } else {
        errors.email = ''
      }
      break
    case 'firstName':
      if (!formData.firstName) {
        errors.firstName = t('auth.firstNameRequired')
      } else {
        errors.firstName = ''
      }
      break
    case 'lastName':
      if (!formData.lastName) {
        errors.lastName = t('auth.lastNameRequired')
      } else {
        errors.lastName = ''
      }
      break
    case 'password':
      if (!formData.password) {
        errors.password = t('auth.passwordRequired')
      } else if (formData.password.length < 8) {
        errors.password = t('auth.passwordMinLength')
      } else {
        errors.password = ''
      }
      break
    case 'confirmPassword':
      if (!formData.confirmPassword) {
        errors.confirmPassword = t('auth.confirmPasswordRequired')
      } else if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = t('auth.passwordMismatch')
      } else {
        errors.confirmPassword = ''
      }
      break
    case 'agreeTerms':
      if (!formData.agreeTerms) {
        errors.agreeTerms = t('auth.mustAgreeTerms')
      } else {
        errors.agreeTerms = ''
      }
      break
  }
}

// Watch password changes to revalidate confirm password
watch(() => formData.password, () => {
  if (formData.confirmPassword) {
    validateField('confirmPassword')
  }
})

const handleSubmit = () => {
  // Validate all fields
  Object.keys(formData).forEach(field => {
    validateField(field)
  })

  if (isFormValid.value) {
    registerError.value = ''
    emit('submit', {
      username: formData.username,
      email: formData.email,
      first_name: formData.firstName,
      last_name: formData.lastName,
      password: formData.password
    })
  }
}

// Expose methods to parent
defineExpose({
  setError: (error) => {
    registerError.value = error
  },
  clearForm: () => {
    Object.keys(formData).forEach(key => {
      if (typeof formData[key] === 'boolean') {
        formData[key] = false
      } else {
        formData[key] = ''
      }
    })
    Object.keys(errors).forEach(key => {
      errors[key] = ''
    })
    registerError.value = ''
  }
})
</script>

<style scoped>
.register-form {
  max-width: 500px;
  margin: 0 auto;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 2rem;
}

.register-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.register-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group--half {
  flex: 1;
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

.password-strength {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.strength-indicator {
  display: flex;
  gap: 2px;
}

.strength-bar {
  width: 1rem;
  height: 3px;
  background-color: #e5e7eb;
  border-radius: 2px;
}

.strength-none .strength-bar {
  background-color: #e5e7eb;
}

.strength-weak .strength-bar:nth-child(1) {
  background-color: #ef4444;
}

.strength-medium .strength-bar:nth-child(-n+2) {
  background-color: #f59e0b;
}

.strength-strong .strength-bar {
  background-color: #10b981;
}

.strength-text {
  font-size: 0.75rem;
  color: #6b7280;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
  line-height: 1.5;
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
  margin-top: 0.25rem;
  position: relative;
  background: white;
  flex-shrink: 0;
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

.register-button {
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

.register-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.register-button:disabled {
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

.register-error {
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
  color: #6b7280;
}

.link {
  color: #3b82f6;
  text-decoration: none;
  margin-left: 0.25rem;
}

.link:hover {
  text-decoration: underline;
}
</style>