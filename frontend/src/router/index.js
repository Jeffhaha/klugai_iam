/**
 * 独立IAM认证服务 - 路由配置
 * Independent IAM Authentication Service - Router Configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Lazy load components
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Profile = () => import('@/views/Profile.vue')
const Sessions = () => import('@/views/Sessions.vue')
const Admin = () => import('@/views/Admin.vue')
const NotFound = () => import('@/views/NotFound.vue')
const Unauthorized = () => import('@/views/Unauthorized.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: 'Login',
      requiresAuth: false,
      hideForAuth: true // Hide this route if user is already authenticated
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'Dashboard',
      requiresAuth: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: {
      title: 'Profile',
      requiresAuth: true
    }
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: Sessions,
    meta: {
      title: 'Sessions',
      requiresAuth: true
    }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: {
      title: 'Admin',
      requiresAuth: true,
      requiresRoles: ['admin']
    }
  },
  {
    path: '/unauthorized',
    name: 'Unauthorized',
    component: Unauthorized,
    meta: {
      title: 'Unauthorized',
      requiresAuth: false
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: 'Not Found',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top when changing routes
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Global navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Wait for auth store to initialize
  if (!authStore.initialized) {
    await new Promise(resolve => {
      const unwatch = authStore.$watch('initialized', (initialized) => {
        if (initialized) {
          unwatch()
          resolve()
        }
      })
    })
  }

  // Update document title
  document.title = to.meta.title ? `${to.meta.title} - IAM Service` : 'IAM Service'

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      // Redirect to login with return URL
      next({
        name: 'Login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // Check role requirements
    if (to.meta.requiresRoles) {
      const hasRequiredRole = to.meta.requiresRoles.some(role => 
        authStore.hasRole(role)
      )
      
      if (!hasRequiredRole) {
        next({ name: 'Unauthorized' })
        return
      }
    }

    // Check permission requirements
    if (to.meta.requiresPermissions) {
      const hasRequiredPermission = to.meta.requiresPermissions.some(permission =>
        authStore.hasPermission(permission)
      )
      
      if (!hasRequiredPermission) {
        next({ name: 'Unauthorized' })
        return
      }
    }
  }

  // Hide route for authenticated users (like login page)
  if (to.meta.hideForAuth && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

// Global after navigation
router.afterEach((to, from) => {
  // Log navigation for debugging
  if (import.meta.env.DEV) {
    console.log(`Navigation: ${from.path || '/'} -> ${to.path}`)
  }
})

// Error handling for navigation
router.onError((error) => {
  console.error('Router error:', error)
  
  // You can handle specific routing errors here
  if (error.message.includes('ChunkLoadError')) {
    // Handle chunk loading errors (when lazy-loaded components fail)
    window.location.reload()
  }
})

export default router