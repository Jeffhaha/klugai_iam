/**
 * 独立IAM认证服务 - HTTP客户端配置
 * Independent IAM Authentication Service - HTTP Client Configuration
 */

import axios from 'axios'
import { tokenService } from '@/utils/tokenService'

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const tokens = tokenService.getTokens()
    if (tokens.accessToken) {
      config.headers.Authorization = `Bearer ${tokens.accessToken}`
    }

    // Add request timestamp
    config.metadata = { startTime: Date.now() }

    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - Handle common responses and errors
apiClient.interceptors.response.use(
  (response) => {
    // Log request duration
    const duration = Date.now() - response.config.metadata.startTime
    console.debug(`API Request: ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`)

    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Log error details
    console.error('API Error:', {
      url: originalRequest?.url,
      method: originalRequest?.method,
      status: error.response?.status,
      message: error.response?.data?.error?.message || error.message
    })

    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const tokens = tokenService.getTokens()
        if (tokens.refreshToken) {
          // Try to refresh token
          const refreshResponse = await axios.post(
            `${apiClient.defaults.baseURL}/api/v1/auth/refresh`,
            { refresh_token: tokens.refreshToken }
          )

          if (refreshResponse.data?.access_token) {
            // Update tokens
            tokenService.setTokens(
              refreshResponse.data.access_token,
              refreshResponse.data.refresh_token || tokens.refreshToken
            )

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`
            return apiClient(originalRequest)
          }
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)
        // Clear invalid tokens
        tokenService.clearTokens()
        
        // Redirect to login if we're in a browser environment
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
    }

    // Handle 403 Forbidden - Insufficient permissions
    if (error.response?.status === 403) {
      // You can handle permission errors here
      console.warn('Access denied:', error.response.data?.error?.message)
    }

    // Handle 429 Too Many Requests - Rate limiting
    if (error.response?.status === 429) {
      console.warn('Rate limit exceeded, retrying after delay')
      
      // Get retry delay from headers or use default
      const retryAfter = error.response.headers['retry-after'] || 1000
      
      // Wait and retry once
      if (!originalRequest._rateLimitRetry) {
        originalRequest._rateLimitRetry = true
        await new Promise(resolve => setTimeout(resolve, retryAfter))
        return apiClient(originalRequest)
      }
    }

    // Handle 500+ Server errors
    if (error.response?.status >= 500) {
      console.error('Server error:', error.response.status, error.response.data)
      
      // You can add server error handling here
      // For example, show a global error message
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message)
      
      // You can add network error handling here
      // For example, show offline message
    }

    return Promise.reject(error)
  }
)

// Helper function to check if we're in development
export const isDevelopment = import.meta.env.DEV

// Helper function to get API base URL
export const getApiBaseUrl = () => apiClient.defaults.baseURL

// Helper function to set API base URL (for dynamic configuration)
export const setApiBaseUrl = (baseURL) => {
  apiClient.defaults.baseURL = baseURL
}

// Helper function to add custom headers
export const setCustomHeaders = (headers) => {
  Object.assign(apiClient.defaults.headers, headers)
}

// Helper function to create a request with custom config
export const createRequest = (config) => {
  return apiClient.create({
    ...apiClient.defaults,
    ...config
  })
}

// Export configured axios instance as default
export default apiClient