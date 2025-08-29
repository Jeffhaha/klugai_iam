/**
 * 独立IAM认证服务 - 认证状态管理
 * Independent IAM Authentication Service - Auth Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { tokenService } from '@/utils/tokenService'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const accessToken = ref(null)
  const refreshToken = ref(null)
  const loading = ref(false)
  const initialized = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)
  const userRoles = computed(() => user.value?.roles || [])
  const userPermissions = computed(() => user.value?.permissions || [])
  const isAdmin = computed(() => userRoles.value.includes('admin'))
  const displayName = computed(() => {
    if (!user.value) return ''
    return user.value.display_name || user.value.username || `${user.value.first_name} ${user.value.last_name}`.trim()
  })

  // Actions
  const login = async (credentials) => {
    try {
      loading.value = true

      const response = await authApi.login(credentials)
      
      if (response.success) {
        // Store tokens
        accessToken.value = response.access_token
        refreshToken.value = response.refresh_token
        user.value = response.user

        // Save tokens to local storage
        tokenService.setTokens(response.access_token, response.refresh_token)
        
        // Save user data
        localStorage.setItem('user', JSON.stringify(response.user))

        return { success: true }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('Login error:', error)
      return { 
        success: false, 
        message: error.response?.data?.error?.message || 'Login failed' 
      }
    } finally {
      loading.value = false
    }
  }

  const register = async (userData) => {
    try {
      loading.value = true

      const response = await authApi.register(userData)
      
      if (response.success) {
        return { success: true, message: response.message }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('Register error:', error)
      return { 
        success: false, 
        message: error.response?.data?.error?.message || 'Registration failed' 
      }
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      loading.value = true

      // Call logout API if token exists
      if (accessToken.value) {
        await authApi.logout()
      }
    } catch (error) {
      console.error('Logout API error:', error)
      // Continue with local logout even if API fails
    } finally {
      // Clear local state
      clearAuthData()
      loading.value = false
    }
  }

  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('No refresh token available')
      }

      const response = await authApi.refreshToken(refreshToken.value)
      
      if (response.success) {
        accessToken.value = response.access_token
        
        // Update refresh token if provided
        if (response.refresh_token) {
          refreshToken.value = response.refresh_token
        }

        // Save new tokens
        tokenService.setTokens(accessToken.value, refreshToken.value)
        
        return true
      } else {
        throw new Error('Token refresh failed')
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      // If refresh fails, logout user
      await logout()
      return false
    }
  }

  const validateToken = async () => {
    try {
      if (!accessToken.value) {
        return false
      }

      const response = await authApi.validateToken()
      
      if (response.valid) {
        return true
      } else {
        // Token is invalid, try to refresh
        return await refreshAccessToken()
      }
    } catch (error) {
      console.error('Token validation error:', error)
      return false
    }
  }

  const fetchUserProfile = async () => {
    try {
      const response = await authApi.getUserProfile()
      
      if (response.success) {
        user.value = response.user
        localStorage.setItem('user', JSON.stringify(response.user))
        return true
      } else {
        throw new Error('Failed to fetch user profile')
      }
    } catch (error) {
      console.error('Fetch user profile error:', error)
      return false
    }
  }

  const updateUserProfile = async (updateData) => {
    try {
      loading.value = true

      const response = await authApi.updateUserProfile(updateData)
      
      if (response.success) {
        user.value = response.user
        localStorage.setItem('user', JSON.stringify(response.user))
        return { success: true }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('Update profile error:', error)
      return { 
        success: false, 
        message: error.response?.data?.error?.message || 'Profile update failed' 
      }
    } finally {
      loading.value = false
    }
  }

  const changePassword = async (passwordData) => {
    try {
      loading.value = true

      const response = await authApi.changePassword(passwordData)
      
      if (response.success) {
        // Force re-login after password change
        await logout()
        return { success: true, requireLogin: true }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('Change password error:', error)
      return { 
        success: false, 
        message: error.response?.data?.error?.message || 'Password change failed' 
      }
    } finally {
      loading.value = false
    }
  }

  const forgotPassword = async (emailData) => {
    try {
      loading.value = true

      const response = await authApi.forgotPassword(emailData)
      
      if (response.success) {
        return { success: true, message: response.message }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('Forgot password error:', error)
      return { 
        success: false, 
        message: error.response?.data?.error?.message || 'Forgot password failed' 
      }
    } finally {
      loading.value = false
    }
  }

  const hasPermission = (permission) => {
    return userPermissions.value.includes(permission) || isAdmin.value
  }

  const hasRole = (role) => {
    return userRoles.value.includes(role)
  }

  const hasAnyRole = (roles) => {
    return roles.some(role => userRoles.value.includes(role))
  }

  const clearAuthData = () => {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    
    // Clear local storage
    tokenService.clearTokens()
    localStorage.removeItem('user')
  }

  const initialize = async () => {
    try {
      // Try to restore tokens from local storage
      const tokens = tokenService.getTokens()
      
      if (tokens.accessToken && tokens.refreshToken) {
        accessToken.value = tokens.accessToken
        refreshToken.value = tokens.refreshToken

        // Try to restore user data
        const savedUser = localStorage.getItem('user')
        if (savedUser) {
          user.value = JSON.parse(savedUser)
        }

        // Validate the token
        const isValid = await validateToken()
        
        if (isValid && !user.value) {
          // If token is valid but no user data, fetch it
          await fetchUserProfile()
        }

        if (!isValid) {
          clearAuthData()
        }
      }
    } catch (error) {
      console.error('Auth initialization error:', error)
      clearAuthData()
    } finally {
      initialized.value = true
    }
  }

  // Initialize auth state on store creation
  initialize()

  return {
    // State
    user,
    accessToken,
    refreshToken,
    loading,
    initialized,
    
    // Getters
    isLoggedIn,
    userRoles,
    userPermissions,
    isAdmin,
    displayName,
    
    // Actions
    login,
    register,
    logout,
    refreshAccessToken,
    validateToken,
    fetchUserProfile,
    updateUserProfile,
    changePassword,
    forgotPassword,
    hasPermission,
    hasRole,
    hasAnyRole,
    clearAuthData,
    initialize
  }
})