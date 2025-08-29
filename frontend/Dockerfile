# =============================================================================
# 独立IAM认证授权服务 - 前端Dockerfile
# Independent IAM Authentication & Authorization Service - Frontend
# =============================================================================

# 构建阶段
FROM node:18-alpine AS builder

# 设置构建参数
ARG NODE_ENV=production
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_APP_TITLE=IAM Service
ARG VITE_APP_DESCRIPTION="Independent IAM Authentication & Authorization Service"

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci --only=production --frozen-lockfile && npm cache clean --force

# 复制源代码
COPY . .

# 设置环境变量
ENV NODE_ENV=$NODE_ENV
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_APP_TITLE=$VITE_APP_TITLE
ENV VITE_APP_DESCRIPTION=$VITE_APP_DESCRIPTION

# 构建应用
RUN npm run build

# =============================================================================
# 生产阶段
# =============================================================================

FROM nginx:alpine AS runtime

# 安装必要的包
RUN apk add --no-cache curl

# 创建nginx用户和组
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx.default.conf /etc/nginx/conf.d/default.conf

# 创建日志目录并设置权限
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d

# 创建pid文件目录
RUN mkdir -p /var/run && \
    chown nginx:nginx /var/run

# 修改nginx配置以使用非特权端口
RUN sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf

# 切换到非root用户
USER nginx

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# 暴露端口
EXPOSE 8080

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]