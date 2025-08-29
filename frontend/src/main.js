/**
 * 独立IAM认证服务 - 应用入口
 * Independent IAM Authentication Service - Application Entry Point
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createHead } from '@vueuse/head'
import router from './router'
import i18n from './i18n'
import App from './App.vue'

// Import global styles
import './styles/main.scss'

// Create Vue app
const app = createApp(App)

// Setup Pinia store
const pinia = createPinia()
app.use(pinia)

// Setup Vue Router
app.use(router)

// Setup i18n
app.use(i18n)

// Setup head management
const head = createHead()
app.use(head)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Global error:', error, info)
  
  // You can add error reporting service here
  // Example: errorReportingService.report(error, { instance, info })
}

// Global warning handler (development only)
if (import.meta.env.DEV) {
  app.config.warnHandler = (msg, instance, trace) => {
    console.warn('Vue warning:', msg, trace)
  }
}

// Mount app
app.mount('#app')

// Export app for potential testing or debugging
export default app