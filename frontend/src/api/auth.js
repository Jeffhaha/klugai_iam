/**
 * 独立IAM认证服务 - 认证API接口
 * Independent IAM Authentication Service - Auth API
 */

import { apiClient } from './client'

export const authApi = {
  /**
   * 用户登录
   * @param {Object} credentials - 登录凭据
   * @param {string} credentials.username - 用户名或邮箱
   * @param {string} credentials.password - 密码
   * @param {boolean} credentials.rememberMe - 记住我
   */
  async login(credentials) {
    try {
      const response = await apiClient.post('/api/v1/auth/login', {
        username: credentials.username,
        password: credentials.password,
        remember_me: credentials.rememberMe
      })

      return {
        success: true,
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        token_type: response.data.token_type,
        expires_in: response.data.expires_in,
        user: response.data.user,
        session_id: response.data.session_id
      }
    } catch (error) {
      console.error('Login API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Login failed'
      }
    }
  },

  /**
   * 用户注册
   * @param {Object} userData - 用户数据
   */
  async register(userData) {
    try {
      const response = await apiClient.post('/api/v1/auth/register', userData)

      return {
        success: true,
        message: response.data.message,
        user_id: response.data.user_id
      }
    } catch (error) {
      console.error('Register API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Registration failed'
      }
    }
  },

  /**
   * 用户登出
   */
  async logout() {
    try {
      await apiClient.post('/api/v1/auth/logout')
      return { success: true }
    } catch (error) {
      console.error('Logout API error:', error)
      // Don't throw error for logout, just log it
      return { success: false }
    }
  },

  /**
   * 刷新访问令牌
   * @param {string} refreshToken - 刷新令牌
   */
  async refreshToken(refreshToken) {
    try {
      const response = await apiClient.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      })

      return {
        success: true,
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        token_type: response.data.token_type,
        expires_in: response.data.expires_in
      }
    } catch (error) {
      console.error('Refresh token API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Token refresh failed'
      }
    }
  },

  /**
   * 验证访问令牌
   */
  async validateToken() {
    try {
      const response = await apiClient.get('/api/v1/auth/validate')

      return {
        valid: response.data.valid,
        user_id: response.data.user_id,
        expires_at: response.data.expires_at,
        scopes: response.data.scopes || []
      }
    } catch (error) {
      console.error('Validate token API error:', error)
      return {
        valid: false,
        error_message: error.response?.data?.error?.message
      }
    }
  },

  /**
   * 获取当前用户信息
   */
  async getUserProfile() {
    try {
      const response = await apiClient.get('/api/v1/users/me')

      return {
        success: true,
        user: response.data
      }
    } catch (error) {
      console.error('Get user profile API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Failed to get user profile'
      }
    }
  },

  /**
   * 更新当前用户信息
   * @param {Object} updateData - 更新数据
   */
  async updateUserProfile(updateData) {
    try {
      const response = await apiClient.put('/api/v1/users/me', updateData)

      return {
        success: true,
        user: response.data,
        message: 'Profile updated successfully'
      }
    } catch (error) {
      console.error('Update user profile API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Profile update failed'
      }
    }
  },

  /**
   * 修改密码
   * @param {Object} passwordData - 密码数据
   * @param {string} passwordData.currentPassword - 当前密码
   * @param {string} passwordData.newPassword - 新密码
   */
  async changePassword(passwordData) {
    try {
      const response = await apiClient.post('/api/v1/users/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      })

      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      console.error('Change password API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Password change failed'
      }
    }
  },

  /**
   * 忘记密码
   * @param {Object} emailData - 邮箱数据
   * @param {string} emailData.email - 邮箱地址
   */
  async forgotPassword(emailData) {
    try {
      const response = await apiClient.post('/api/v1/auth/forgot-password', {
        email: emailData.email
      })

      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      console.error('Forgot password API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Forgot password failed'
      }
    }
  },

  /**
   * 重置密码
   * @param {Object} resetData - 重置密码数据
   * @param {string} resetData.token - 重置令牌
   * @param {string} resetData.newPassword - 新密码
   */
  async resetPassword(resetData) {
    try {
      const response = await apiClient.post('/api/v1/auth/reset-password', {
        token: resetData.token,
        new_password: resetData.newPassword
      })

      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      console.error('Reset password API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Password reset failed'
      }
    }
  },

  /**
   * 获取用户会话列表
   */
  async getUserSessions() {
    try {
      const response = await apiClient.get('/api/v1/sessions/me')

      return {
        success: true,
        sessions: response.data.sessions
      }
    } catch (error) {
      console.error('Get user sessions API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Failed to get sessions'
      }
    }
  },

  /**
   * 结束特定会话
   * @param {string} sessionId - 会话ID
   */
  async endSession(sessionId) {
    try {
      const response = await apiClient.delete(`/api/v1/sessions/${sessionId}`)

      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      console.error('End session API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Failed to end session'
      }
    }
  },

  /**
   * 结束所有会话
   */
  async endAllSessions() {
    try {
      const response = await apiClient.delete('/api/v1/sessions/all')

      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      console.error('End all sessions API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Failed to end sessions'
      }
    }
  },

  /**
   * 检查授权权限
   * @param {Object} authzRequest - 授权请求
   * @param {string} authzRequest.resource - 资源
   * @param {string} authzRequest.action - 操作
   * @param {Object} authzRequest.context - 上下文
   */
  async checkAuthorization(authzRequest) {
    try {
      const response = await apiClient.post('/api/v1/authz/authorize', authzRequest)

      return {
        success: response.data.success,
        decision: response.data.decision,
        request_id: response.data.request_id
      }
    } catch (error) {
      console.error('Check authorization API error:', error)
      return {
        success: false,
        decision: {
          effect: 'deny',
          reason: 'Authorization check failed',
          attributes_used: [],
          evaluation_time_ms: 0,
          cache_hit: false,
          obligations: [],
          advice: ['Authorization service unavailable'],
          timestamp: new Date().toISOString()
        }
      }
    }
  },

  /**
   * 批量授权检查
   * @param {Object} bulkRequest - 批量授权请求
   */
  async checkBulkAuthorization(bulkRequest) {
    try {
      const response = await apiClient.post('/api/v1/authz/authorize/bulk', bulkRequest)

      return {
        success: true,
        results: response.data.results,
        summary: response.data.summary
      }
    } catch (error) {
      console.error('Bulk authorization API error:', error)
      return {
        success: false,
        message: error.response?.data?.error?.message || 'Bulk authorization failed'
      }
    }
  }
}