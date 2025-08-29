# 独立IAM认证授权服务 - 前端应用

Independent IAM Authentication & Authorization Service - Frontend Application

## 项目概述 / Project Overview

这是一个完全独立的IAM认证授权服务的前端应用，提供完整的用户认证、授权管理和用户界面。

This is a completely independent frontend application for IAM authentication and authorization service, providing comprehensive user authentication, authorization management, and user interface.

## 核心功能 / Core Features

### 🔐 认证功能 / Authentication Features
- 用户登录/注册 / User login/registration
- JWT令牌管理 / JWT token management  
- 会话管理 / Session management
- 密码重置 / Password reset
- 记住登录状态 / Remember login state

### 🛡️ 授权功能 / Authorization Features
- 基于角色的访问控制 (RBAC) / Role-based access control
- 基于属性的访问控制 (ABAC) / Attribute-based access control
- 权限检查 / Permission checking
- 路由守卫 / Route guards

### 🎨 用户界面 / User Interface
- 响应式设计 / Responsive design
- 多语言支持 (中文/英文) / Multi-language support (Chinese/English)
- 现代化UI组件 / Modern UI components
- 深色/浅色主题 / Dark/Light theme support

### 📱 移动端支持 / Mobile Support
- 移动端适配 / Mobile responsive
- 触摸友好的交互 / Touch-friendly interactions
- PWA支持 / PWA support

## 技术栈 / Technology Stack

### 核心框架 / Core Framework
- **Vue 3** - 渐进式JavaScript框架
- **Vue Router 4** - 官方路由管理器
- **Pinia** - 状态管理库
- **TypeScript** - 类型安全的JavaScript

### 构建工具 / Build Tools
- **Vite** - 快速构建工具
- **ESLint** - 代码质量检查
- **Prettier** - 代码格式化

### UI组件 / UI Components
- **自定义组件库** / Custom component library
- **CSS3 / SCSS** - 样式预处理器
- **响应式设计** / Responsive design

### 工具库 / Utility Libraries
- **Axios** - HTTP客户端
- **VueUse** - Vue组合式API工具集
- **Vue I18n** - 国际化解决方案

## 项目结构 / Project Structure

```
frontend/
├── public/                 # 静态资源
│   ├── favicon.ico
│   └── index.html
├── src/                    # 源代码
│   ├── api/               # API接口
│   │   ├── auth.js        # 认证API
│   │   └── client.js      # HTTP客户端
│   ├── assets/            # 资源文件
│   ├── components/        # 可复用组件
│   │   ├── Auth/          # 认证相关组件
│   │   ├── Common/        # 通用组件
│   │   └── Layout/        # 布局组件
│   ├── i18n/              # 国际化
│   │   ├── locales/       # 语言包
│   │   └── index.js       # i18n配置
│   ├── router/            # 路由配置
│   │   └── index.js       # 路由定义
│   ├── stores/            # Pinia状态管理
│   │   ├── auth.js        # 认证状态
│   │   └── user.js        # 用户状态
│   ├── styles/            # 全局样式
│   │   ├── variables.scss # SCSS变量
│   │   ├── mixins.scss    # SCSS混入
│   │   └── main.scss      # 主样式文件
│   ├── utils/             # 工具函数
│   │   ├── tokenService.js # 令牌管理
│   │   └── helpers.js     # 辅助函数
│   ├── views/             # 页面组件
│   │   ├── Login.vue      # 登录页面
│   │   ├── Dashboard.vue  # 仪表板
│   │   ├── Profile.vue    # 用户资料
│   │   └── Admin.vue      # 管理页面
│   ├── App.vue            # 根组件
│   └── main.js            # 应用入口
├── .env.example           # 环境变量示例
├── .gitignore
├── package.json
├── vite.config.js         # Vite配置
└── README.md
```

## 快速开始 / Quick Start

### 1. 环境要求 / Requirements

- Node.js >= 16.0.0
- npm >= 7.0.0 或 yarn >= 1.22.0

### 2. 安装依赖 / Install Dependencies

```bash
npm install
# 或 / or
yarn install
```

### 3. 环境配置 / Environment Configuration

复制环境变量配置文件：
```bash
cp .env.example .env.local
```

编辑 `.env.local` 文件，配置API服务器地址：
```env
# API服务器地址 / API Server URL
VITE_API_BASE_URL=http://localhost:8000

# 应用标题 / Application Title  
VITE_APP_TITLE=IAM Service

# 应用描述 / Application Description
VITE_APP_DESCRIPTION=Independent IAM Authentication & Authorization Service
```

### 4. 启动开发服务器 / Start Development Server

```bash
npm run dev
# 或 / or
yarn dev
```

应用将在 `http://localhost:5173` 启动。

### 5. 构建生产版本 / Build for Production

```bash
npm run build
# 或 / or
yarn build
```

构建文件将生成在 `dist/` 目录中。

### 6. 预览生产版本 / Preview Production Build

```bash
npm run preview  
# 或 / or
yarn preview
```

## 开发指南 / Development Guide

### 组件开发 / Component Development

#### 创建新组件 / Creating New Components

```vue
<template>
  <div class="my-component">
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})

// Reactive data
const isVisible = ref(true)

// Computed properties
const classes = computed(() => ({
  'my-component': true,
  'my-component--visible': isVisible.value
}))

// Methods
const toggle = () => {
  isVisible.value = !isVisible.value
}

// Expose methods to parent
defineExpose({
  toggle
})
</script>

<style scoped>
.my-component {
  padding: 1rem;
  border-radius: 8px;
  background: white;
}

.my-component--visible {
  opacity: 1;
}
</style>
```

### 状态管理 / State Management

#### 使用Pinia Store / Using Pinia Store

```javascript
import { useAuthStore } from '@/stores/auth'

export default {
  setup() {
    const authStore = useAuthStore()
    
    // 访问状态 / Access state
    const isLoggedIn = computed(() => authStore.isLoggedIn)
    const user = computed(() => authStore.user)
    
    // 调用方法 / Call methods
    const login = async (credentials) => {
      const result = await authStore.login(credentials)
      return result
    }
    
    return {
      isLoggedIn,
      user,
      login
    }
  }
}
```

### 路由配置 / Route Configuration

#### 添加新路由 / Adding New Routes

```javascript
// router/index.js
const routes = [
  {
    path: '/new-page',
    name: 'NewPage',
    component: () => import('@/views/NewPage.vue'),
    meta: {
      title: 'New Page',
      requiresAuth: true,
      requiresRoles: ['admin']
    }
  }
]
```

### API接口 / API Integration

#### 调用API / Making API Calls

```javascript
import { authApi } from '@/api/auth'

export default {
  setup() {
    const loading = ref(false)
    const error = ref(null)
    
    const fetchUserProfile = async () => {
      try {
        loading.value = true
        error.value = null
        
        const response = await authApi.getUserProfile()
        
        if (response.success) {
          return response.user
        } else {
          throw new Error(response.message)
        }
      } catch (err) {
        error.value = err.message
        throw err
      } finally {
        loading.value = false
      }
    }
    
    return {
      loading,
      error,
      fetchUserProfile
    }
  }
}
```

## 部署指南 / Deployment Guide

### 1. 构建生产版本 / Build Production

```bash
npm run build
```

### 2. 静态文件部署 / Static File Deployment

构建完成后，将 `dist/` 目录中的文件部署到你的Web服务器。

#### Nginx配置示例 / Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/iam-frontend/dist;
    index index.html;

    # 处理Vue Router的History模式 / Handle Vue Router history mode
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存 / Static assets caching
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API代理 / API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 3. Docker部署 / Docker Deployment

#### Dockerfile

```dockerfile
# 构建阶段 / Build stage
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# 生产阶段 / Production stage
FROM nginx:alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 构建和运行 / Build and Run

```bash
# 构建镜像 / Build image
docker build -t iam-frontend .

# 运行容器 / Run container
docker run -p 80:80 iam-frontend
```

## 配置选项 / Configuration Options

### 环境变量 / Environment Variables

| 变量名 / Variable | 默认值 / Default | 说明 / Description |
|-------------------|------------------|-------------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | API服务器地址 / API server URL |
| `VITE_APP_TITLE` | `IAM Service` | 应用标题 / Application title |
| `VITE_APP_DESCRIPTION` | `Independent IAM Service` | 应用描述 / Application description |
| `VITE_ENABLE_PWA` | `false` | 启用PWA / Enable PWA |
| `VITE_DEFAULT_LOCALE` | `en` | 默认语言 / Default language |

### 主题配置 / Theme Configuration

```scss
// styles/variables.scss
:root {
  // 主色调 / Primary colors
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
  --color-primary-light: #60a5fa;
  
  // 次要色调 / Secondary colors
  --color-secondary: #64748b;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  
  // 中性色 / Neutral colors
  --color-gray-50: #f8fafc;
  --color-gray-100: #f1f5f9;
  --color-gray-900: #0f172a;
  
  // 字体 / Typography
  --font-family-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-size-base: 1rem;
  --line-height-base: 1.5;
  
  // 间距 / Spacing
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 3rem;
  
  // 边框半径 / Border radius
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  
  // 阴影 / Shadows
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
```

## 国际化 / Internationalization

### 添加新语言 / Adding New Languages

1. 在 `src/i18n/locales/` 目录创建语言文件：

```javascript
// src/i18n/locales/fr.js
export default {
  auth: {
    login: 'Se connecter',
    register: 'S\'inscrire',
    logout: 'Se déconnecter',
    username: 'Nom d\'utilisateur',
    password: 'Mot de passe',
    // ... 更多翻译
  },
  common: {
    loading: 'Chargement...',
    save: 'Sauvegarder',
    cancel: 'Annuler',
    // ... 更多翻译
  }
}
```

2. 在 `src/i18n/index.js` 中注册：

```javascript
import fr from './locales/fr'

const messages = {
  en,
  'zh-CN': zhCN,
  fr // 添加新语言
}
```

### 使用翻译 / Using Translations

```vue
<template>
  <div>
    <h1>{{ $t('auth.login') }}</h1>
    <p>{{ $t('common.welcome', { name: userName }) }}</p>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

// 在JavaScript中使用 / Use in JavaScript
const message = t('auth.loginSuccess')

// 切换语言 / Switch language
const changeLanguage = (newLocale) => {
  locale.value = newLocale
}
</script>
```

## 性能优化 / Performance Optimization

### 代码分割 / Code Splitting

```javascript
// 路由级别的代码分割 / Route-level code splitting
const Dashboard = () => import('@/views/Dashboard.vue')
const Profile = () => import('@/views/Profile.vue')

// 组件级别的懒加载 / Component-level lazy loading
const HeavyComponent = defineAsyncComponent(() => 
  import('@/components/HeavyComponent.vue')
)
```

### 缓存策略 / Caching Strategy

```javascript
// 服务工作器缓存 / Service Worker caching
// vite.config.js
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours
              }
            }
          }
        ]
      }
    })
  ]
})
```

## 测试 / Testing

### 单元测试 / Unit Tests

```javascript
// tests/components/LoginForm.spec.js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import LoginForm from '@/components/Auth/LoginForm.vue'

describe('LoginForm', () => {
  it('renders login form correctly', () => {
    const wrapper = mount(LoginForm)
    
    expect(wrapper.find('[data-testid="username-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="password-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-button"]').exists()).toBe(true)
  })
  
  it('validates required fields', async () => {
    const wrapper = mount(LoginForm)
    
    await wrapper.find('[data-testid="login-button"]').trigger('click')
    
    expect(wrapper.find('.form-error').text()).toContain('Username is required')
  })
})
```

### 端到端测试 / E2E Tests

```javascript
// e2e/auth.spec.js
import { test, expect } from '@playwright/test'

test('user can login successfully', async ({ page }) => {
  await page.goto('/login')
  
  await page.fill('[data-testid="username-input"]', 'testuser')
  await page.fill('[data-testid="password-input"]', 'testpass')
  await page.click('[data-testid="login-button"]')
  
  await expect(page).toHaveURL('/dashboard')
  await expect(page.locator('h1')).toContainText('Dashboard')
})
```

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. API连接问题 / API Connection Issues

**问题**: 无法连接到后端API服务器
**解决方案**:
- 检查 `.env.local` 文件中的 `VITE_API_BASE_URL` 配置
- 确保后端服务器正在运行
- 检查网络连接和防火墙设置

#### 2. 路由问题 / Routing Issues

**问题**: 刷新页面出现404错误
**解决方案**:
- 配置Web服务器支持Vue Router的History模式
- 参考上面的Nginx配置示例

#### 3. 构建问题 / Build Issues

**问题**: 构建失败或内存不足
**解决方案**:
```bash
# 增加Node.js内存限制 / Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### 调试工具 / Debugging Tools

#### Vue DevTools

安装并使用Vue DevTools进行调试：
```bash
# Chrome扩展 / Chrome Extension
# https://chrome.google.com/webstore/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd

# Firefox扩展 / Firefox Extension  
# https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/
```

#### 开发者工具 / Developer Tools

```javascript
// 开发环境下的全局调试变量 / Global debug variables in development
if (import.meta.env.DEV) {
  window.$app = {
    authStore: useAuthStore(),
    router,
    // ... 其他调试工具
  }
}
```

## 贡献指南 / Contributing

### 开发流程 / Development Workflow

1. Fork项目仓库 / Fork the repository
2. 创建特性分支 / Create a feature branch
```bash
git checkout -b feature/new-feature
```
3. 提交更改 / Make your changes
4. 运行测试 / Run tests
```bash
npm run test
```
5. 提交代码 / Commit your changes
```bash
git commit -m "feat: add new feature"
```
6. 推送分支 / Push to branch
```bash
git push origin feature/new-feature
```
7. 创建Pull Request / Create a Pull Request

### 代码规范 / Code Standards

- 使用ESLint进行代码质量检查
- 使用Prettier进行代码格式化
- 遵循Vue 3组合式API最佳实践
- 编写有意义的提交消息

### 提交消息规范 / Commit Message Convention

使用[Conventional Commits](https://www.conventionalcommits.org/)规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型包括：
- `feat`: 新功能
- `fix`: 错误修复  
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构代码
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动

## 许可证 / License

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 支持 / Support

如有问题或建议，请：

1. 查看[常见问题](#故障排除--troubleshooting)
2. 搜索[已有Issue](https://github.com/your-org/reusable-iam-auth-service/issues)
3. 创建[新Issue](https://github.com/your-org/reusable-iam-auth-service/issues/new)
4. 联系开发团队

## 更新日志 / Changelog

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

---

**独立IAM认证授权服务前端** - 为现代Web应用提供安全、可靠的认证授权解决方案。

**Independent IAM Authentication & Authorization Frontend** - Secure and reliable authentication & authorization solution for modern web applications.