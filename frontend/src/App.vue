<!--
独立IAM认证服务 - 根应用组件
Independent IAM Authentication Service - Root App Component
-->

<template>
  <div id="app" class="app">
    <!-- Global loading overlay -->
    <div v-if="globalLoading" class="global-loading">
      <div class="loading-spinner"></div>
      <p class="loading-text">{{ $t('common.loading') }}</p>
    </div>

    <!-- Main router view -->
    <router-view v-slot="{ Component, route }">
      <transition name="page" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>

    <!-- Global notifications -->
    <div class="notification-container">
      <transition-group name="notification" tag="div">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'notification',
            `notification--${notification.type}`
          ]"
        >
          <div class="notification-icon">
            <svg v-if="notification.type === 'success'" viewBox="0 0 24 24" class="icon">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <svg v-else-if="notification.type === 'error'" viewBox="0 0 24 24" class="icon">
              <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <svg v-else-if="notification.type === 'warning'" viewBox="0 0 24 24" class="icon">
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" class="icon">
              <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div v-if="notification.message" class="notification-message">
              {{ notification.message }}
            </div>
          </div>
          <button
            class="notification-close"
            @click="dismissNotification(notification.id)"
          >
            <svg viewBox="0 0 24 24" class="icon">
              <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useHead } from '@vueuse/head'
import { useAuthStore } from '@/stores/auth'
import { tokenService } from '@/utils/tokenService'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

// Global state
const globalLoading = ref(true)
const notifications = ref([])
let notificationId = 0

// Head management
useHead({
  title: 'IAM Service',
  meta: [
    { name: 'description', content: 'Independent IAM Authentication & Authorization Service' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { charset: 'utf-8' }
  ],
  link: [
    { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
  ]
})

// Methods
const showNotification = (type, title, message = '', duration = 5000) => {
  const id = ++notificationId
  const notification = {
    id,
    type,
    title,
    message,
    timestamp: Date.now()
  }
  
  notifications.value.push(notification)
  
  // Auto dismiss
  if (duration > 0) {
    setTimeout(() => {
      dismissNotification(id)
    }, duration)
  }
}

const dismissNotification = (id) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

// Global error handler
const handleGlobalError = (error, type = 'error') => {
  console.error('Global error:', error)
  
  let title = t('errors.unexpectedError')
  let message = error.message || t('errors.tryAgainLater')
  
  // Handle specific error types
  if (error.response) {
    const status = error.response.status
    switch (status) {
      case 401:
        title = t('errors.unauthorized')
        message = t('errors.sessionExpired')
        break
      case 403:
        title = t('errors.forbidden')
        message = t('errors.insufficientPermissions')
        break
      case 404:
        title = t('errors.notFound')
        message = t('errors.resourceNotFound')
        break
      case 429:
        title = t('errors.rateLimited')
        message = t('errors.tooManyRequests')
        break
      case 500:
      case 502:
      case 503:
        title = t('errors.serverError')
        message = t('errors.serverUnavailable')
        break
      default:
        message = error.response.data?.error?.message || message
    }
  }
  
  showNotification(type, title, message, 8000)
}

// Network status monitoring
const handleOnline = () => {
  showNotification('success', t('network.backOnline'), '', 3000)
}

const handleOffline = () => {
  showNotification('warning', t('network.offline'), t('network.checkConnection'), 0)
}

// Lifecycle
onMounted(async () => {
  try {
    // Initialize auth store
    if (!authStore.initialized) {
      await authStore.initialize()
    }
    
    // Start token auto-refresh if user is logged in
    if (authStore.isLoggedIn) {
      tokenService.setRefreshCallback(async () => {
        try {
          await authStore.refreshAccessToken()
        } catch (error) {
          console.error('Auto token refresh failed:', error)
          showNotification('warning', t('auth.sessionExpiring'), t('auth.pleaseRelogin'))
        }
      })
      tokenService.startAutoRefresh()
    }
    
    // Add network status listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    // Add global error handler
    window.addEventListener('unhandledrejection', (event) => {
      handleGlobalError(event.reason)
    })
    
    window.addEventListener('error', (event) => {
      handleGlobalError(event.error)
    })
    
  } catch (error) {
    console.error('App initialization error:', error)
    handleGlobalError(error)
  } finally {
    // Hide global loading after initialization
    setTimeout(() => {
      globalLoading.value = false
    }, 500)
  }
})

onBeforeUnmount(() => {
  // Cleanup
  tokenService.stopAutoRefresh()
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})

// Provide global methods for components to use
window.$notify = showNotification
window.$handleError = handleGlobalError

// Export for potential debugging
if (import.meta.env.DEV) {
  window.$app = {
    authStore,
    router,
    showNotification,
    dismissNotification
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

/* Global loading */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading-text {
  color: #64748b;
  font-size: 0.875rem;
  margin: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Page transitions */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Notifications */
.notification-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  max-width: 400px;
}

.notification {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  padding: 1rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  border-left: 4px solid;
  max-width: 100%;
}

.notification--success {
  border-left-color: #10b981;
}

.notification--error {
  border-left-color: #ef4444;
}

.notification--warning {
  border-left-color: #f59e0b;
}

.notification--info {
  border-left-color: #3b82f6;
}

.notification-icon {
  flex-shrink: 0;
}

.notification-icon .icon {
  width: 1.25rem;
  height: 1.25rem;
}

.notification--success .icon {
  color: #10b981;
  fill: currentColor;
}

.notification--error .icon {
  color: #ef4444;
  fill: currentColor;
}

.notification--warning .icon {
  color: #f59e0b;
  fill: currentColor;
}

.notification--info .icon {
  color: #3b82f6;
  fill: currentColor;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 500;
  font-size: 0.875rem;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.notification-message {
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.4;
}

.notification-close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 1rem;
  height: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.notification-close:hover {
  color: #6b7280;
}

.notification-close .icon {
  width: 0.875rem;
  height: 0.875rem;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
}

/* Notification animations */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* Responsive design */
@media (max-width: 640px) {
  .notification-container {
    left: 1rem;
    right: 1rem;
    max-width: none;
  }
  
  .notification {
    margin-bottom: 0.75rem;
  }
}
</style>