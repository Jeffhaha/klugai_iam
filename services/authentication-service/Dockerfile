# =============================================================================
# 独立IAM认证授权服务 - 认证服务Dockerfile
# Independent IAM Authentication & Authorization Service - Authentication Service
# =============================================================================

# 使用Python 3.11作为基础镜像
FROM python:3.11-slim AS builder

# 设置构建参数
ARG BUILD_ENV=production
ARG DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
COPY requirements-dev.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ "$BUILD_ENV" = "development" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    fi

# =============================================================================
# 生产镜像
# =============================================================================

FROM python:3.11-slim AS runtime

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r iam && useradd -r -g iam iam

# 从builder阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 创建应用目录和相关目录
WORKDIR /app
RUN mkdir -p /app/logs /app/config /app/data && \
    chown -R iam:iam /app

# 复制应用代码
COPY --chown=iam:iam . .

# 复制共享模块
COPY --chown=iam:iam ../../shared ./shared/

# 设置权限
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# 切换到非root用户
USER iam

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${AUTH_PORT:-8001}/health || exit 1

# 暴露端口
EXPOSE 8001 9001

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]