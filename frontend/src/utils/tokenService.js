/**
 * 独立IAM认证服务 - 令牌管理服务
 * Independent IAM Authentication Service - Token Management Service
 */

const ACCESS_TOKEN_KEY = 'iam_access_token'
const REFRESH_TOKEN_KEY = 'iam_refresh_token'
const TOKEN_EXPIRY_KEY = 'iam_token_expiry'

export const tokenService = {
  /**
   * 设置访问令牌和刷新令牌
   * @param {string} accessToken - 访问令牌
   * @param {string} refreshToken - 刷新令牌
   * @param {number} expiresIn - 过期时间（秒）
   */
  setTokens(accessToken, refreshToken, expiresIn) {
    try {
      if (accessToken) {
        localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
        
        // Calculate expiry time if provided
        if (expiresIn) {
          const expiryTime = Date.now() + (expiresIn * 1000)
          localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString())
        }
      }
      
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
      }
    } catch (error) {
      console.error('Error saving tokens to localStorage:', error)
    }
  },

  /**
   * 获取访问令牌和刷新令牌
   * @returns {Object} - 包含访问令牌和刷新令牌的对象
   */
  getTokens() {
    try {
      return {
        accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
        refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
        expiryTime: localStorage.getItem(TOKEN_EXPIRY_KEY)
      }
    } catch (error) {
      console.error('Error reading tokens from localStorage:', error)
      return {
        accessToken: null,
        refreshToken: null,
        expiryTime: null
      }
    }
  },

  /**
   * 获取访问令牌
   * @returns {string|null} - 访问令牌
   */
  getAccessToken() {
    try {
      return localStorage.getItem(ACCESS_TOKEN_KEY)
    } catch (error) {
      console.error('Error reading access token from localStorage:', error)
      return null
    }
  },

  /**
   * 获取刷新令牌
   * @returns {string|null} - 刷新令牌
   */
  getRefreshToken() {
    try {
      return localStorage.getItem(REFRESH_TOKEN_KEY)
    } catch (error) {
      console.error('Error reading refresh token from localStorage:', error)
      return null
    }
  },

  /**
   * 清除所有令牌
   */
  clearTokens() {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(TOKEN_EXPIRY_KEY)
    } catch (error) {
      console.error('Error clearing tokens from localStorage:', error)
    }
  },

  /**
   * 检查访问令牌是否存在
   * @returns {boolean} - 是否存在访问令牌
   */
  hasAccessToken() {
    const token = this.getAccessToken()
    return token !== null && token !== undefined && token !== ''
  },

  /**
   * 检查访问令牌是否过期
   * @returns {boolean} - 是否过期
   */
  isAccessTokenExpired() {
    try {
      const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY)
      
      if (!expiryTime) {
        // If no expiry time is stored, assume not expired
        return false
      }
      
      const expiry = parseInt(expiryTime, 10)
      const now = Date.now()
      
      // Add 1 minute buffer to account for clock skew
      const buffer = 60 * 1000
      
      return now >= (expiry - buffer)
    } catch (error) {
      console.error('Error checking token expiry:', error)
      return false
    }
  },

  /**
   * 解析JWT令牌的载荷（不验证签名）
   * @param {string} token - JWT令牌
   * @returns {Object|null} - 令牌载荷
   */
  parseJwtPayload(token) {
    try {
      if (!token) return null
      
      const parts = token.split('.')
      if (parts.length !== 3) return null
      
      const payload = parts[1]
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
      return JSON.parse(decoded)
    } catch (error) {
      console.error('Error parsing JWT payload:', error)
      return null
    }
  },

  /**
   * 从JWT令牌中提取用户信息
   * @param {string} token - JWT令牌
   * @returns {Object|null} - 用户信息
   */
  extractUserFromToken(token) {
    const payload = this.parseJwtPayload(token)
    if (!payload) return null
    
    return {
      userId: payload.sub || payload.user_id,
      username: payload.username,
      email: payload.email,
      roles: payload.roles || [],
      permissions: payload.permissions || [],
      exp: payload.exp,
      iat: payload.iat
    }
  },

  /**
   * 检查令牌是否即将过期（15分钟内）
   * @param {string} token - JWT令牌
   * @returns {boolean} - 是否即将过期
   */
  isTokenExpiringSoon(token) {
    const payload = this.parseJwtPayload(token)
    if (!payload || !payload.exp) return false
    
    const expiryTime = payload.exp * 1000 // Convert to milliseconds
    const now = Date.now()
    const fifteenMinutes = 15 * 60 * 1000
    
    return (expiryTime - now) < fifteenMinutes
  },

  /**
   * 获取令牌剩余时间（毫秒）
   * @param {string} token - JWT令牌
   * @returns {number} - 剩余时间（毫秒）
   */
  getTokenRemainingTime(token) {
    const payload = this.parseJwtPayload(token)
    if (!payload || !payload.exp) return 0
    
    const expiryTime = payload.exp * 1000
    const now = Date.now()
    
    return Math.max(0, expiryTime - now)
  },

  /**
   * 设置令牌刷新回调
   * @param {Function} callback - 回调函数
   */
  setRefreshCallback(callback) {
    this.refreshCallback = callback
  },

  /**
   * 启动自动令牌刷新
   */
  startAutoRefresh() {
    // Clear existing interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }

    // Check every minute
    this.refreshInterval = setInterval(() => {
      const accessToken = this.getAccessToken()
      
      if (accessToken && this.isTokenExpiringSoon(accessToken)) {
        if (this.refreshCallback) {
          this.refreshCallback()
        }
      }
    }, 60 * 1000) // Check every minute
  },

  /**
   * 停止自动令牌刷新
   */
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
      this.refreshInterval = null
    }
  },

  /**
   * 验证令牌格式
   * @param {string} token - 令牌
   * @returns {boolean} - 是否有效格式
   */
  isValidTokenFormat(token) {
    if (!token || typeof token !== 'string') return false
    
    // Check if it's a JWT token (has 3 parts separated by dots)
    const parts = token.split('.')
    return parts.length === 3
  }
}