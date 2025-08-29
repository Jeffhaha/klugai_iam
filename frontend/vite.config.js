/**
 * 独立IAM认证服务 - Vite配置
 * Independent IAM Authentication Service - Vite Configuration
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Auto import plugins
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'

export default defineConfig({
  plugins: [
    vue(),
    
    // Auto import Vue APIs
    AutoImport({
      imports: [
        'vue',
        'vue-router',
        'vue-i18n',
        'pinia',
        '@vueuse/core',
        '@vueuse/head'
      ],
      dts: true,
      eslintrc: {
        enabled: true,
        filepath: './.eslintrc-auto-import.json',
        globalsPropValue: true
      }
    }),
    
    // Auto import Vue components
    Components({
      dts: true,
      dirs: ['src/components'],
      extensions: ['vue'],
      include: [/\.vue$/, /\.vue\?vue/]
    })
  ],

  // Path resolution
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@api': resolve(__dirname, 'src/api'),
      '@assets': resolve(__dirname, 'src/assets'),
      '@styles': resolve(__dirname, 'src/styles')
    }
  },

  // CSS configuration
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `
          @import "@/styles/variables.scss";
          @import "@/styles/mixins.scss";
        `
      }
    }
  },

  // Development server configuration
  server: {
    host: '0.0.0.0',
    port: 5173,
    open: true,
    proxy: {
      // Proxy API requests to backend
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        timeout: 30000,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('Proxy error:', err)
          })
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url)
          })
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url)
          })
        }
      }
    }
  },

  // Build configuration
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV !== 'production',
    minify: 'esbuild',
    target: 'es2015',
    
    // Rollup options
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['vue-i18n'],
          'utils-vendor': ['axios', '@vueuse/core']
        }
      }
    },
    
    // Optimize dependencies
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'vue-i18n',
        'axios',
        '@vueuse/core'
      ]
    },
    
    // Asset handling
    assetsDir: 'assets',
    assetsInlineLimit: 4096,
    
    // Output file naming
    chunkSizeWarningLimit: 500,
    
    // Build performance
    reportCompressedSize: false
  },

  // Environment variables
  envPrefix: 'VITE_',
  
  // Define global constants
  define: {
    __VUE_OPTIONS_API__: JSON.stringify(false),
    __VUE_PROD_DEVTOOLS__: JSON.stringify(false),
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false)
  },

  // Preview server configuration (for production build)
  preview: {
    host: '0.0.0.0',
    port: 4173,
    open: true
  },

  // ESBuild configuration
  esbuild: {
    // Remove console.log in production
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : []
  }
})