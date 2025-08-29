# =============================================================================
# 独立IAM认证授权服务 - Makefile
# Independent IAM Authentication & Authorization Service - Makefile
# =============================================================================

.PHONY: help build start stop restart logs clean test lint format docker-build docker-push deploy-dev deploy-prod backup restore health migrate seed docs

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
NC := \033[0m # No Color

# 项目配置
PROJECT_NAME := reusable-iam-auth-service
VERSION := $(shell cat VERSION 2>/dev/null || echo "1.0.0")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Docker配置
DOCKER_REGISTRY := your-registry.com
DOCKER_NAMESPACE := iam-service
DOCKER_TAG := $(VERSION)

# 环境配置
ENV_FILE := .env
ENV_EXAMPLE := .env.example

# 服务列表
SERVICES := postgres redis authentication-service authorization-service api-gateway frontend prometheus grafana

##@ 帮助 / Help

help: ## 显示帮助信息 / Show help information
	@echo "$(CYAN)独立IAM认证授权服务 - 管理命令$(NC)"
	@echo "$(CYAN)Independent IAM Authentication & Authorization Service - Management Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 开发环境 / Development

init: ## 初始化开发环境 / Initialize development environment
	@echo "$(YELLOW)正在初始化开发环境... / Initializing development environment...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(BLUE)复制环境变量文件 / Copying environment file...$(NC)"; \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "$(GREEN)请编辑 .env 文件配置你的环境变量 / Please edit .env file to configure your environment variables$(NC)"; \
	fi
	@echo "$(BLUE)检查Docker和Docker Compose... / Checking Docker and Docker Compose...$(NC)"
	@docker --version || (echo "$(RED)错误: 请安装Docker / Error: Please install Docker$(NC)" && exit 1)
	@docker-compose --version || (echo "$(RED)错误: 请安装Docker Compose / Error: Please install Docker Compose$(NC)" && exit 1)
	@echo "$(GREEN)环境初始化完成! / Environment initialization completed!$(NC)"

##@ 构建 / Build

build: ## 构建所有服务镜像 / Build all service images
	@echo "$(YELLOW)构建所有服务镜像... / Building all service images...$(NC)"
	@docker-compose build --parallel
	@echo "$(GREEN)镜像构建完成! / Image build completed!$(NC)"

build-auth: ## 构建认证服务镜像 / Build authentication service image
	@echo "$(YELLOW)构建认证服务镜像... / Building authentication service image...$(NC)"
	@docker-compose build authentication-service
	@echo "$(GREEN)认证服务镜像构建完成! / Authentication service image build completed!$(NC)"

build-authz: ## 构建授权服务镜像 / Build authorization service image
	@echo "$(YELLOW)构建授权服务镜像... / Building authorization service image...$(NC)"
	@docker-compose build authorization-service
	@echo "$(GREEN)授权服务镜像构建完成! / Authorization service image build completed!$(NC)"

build-gateway: ## 构建网关服务镜像 / Build gateway service image
	@echo "$(YELLOW)构建网关服务镜像... / Building gateway service image...$(NC)"
	@docker-compose build api-gateway
	@echo "$(GREEN)网关服务镜像构建完成! / Gateway service image build completed!$(NC)"

build-frontend: ## 构建前端镜像 / Build frontend image
	@echo "$(YELLOW)构建前端镜像... / Building frontend image...$(NC)"
	@docker-compose build frontend
	@echo "$(GREEN)前端镜像构建完成! / Frontend image build completed!$(NC)"

##@ 服务管理 / Service Management

start: ## 启动所有服务 / Start all services
	@echo "$(YELLOW)启动所有服务... / Starting all services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)所有服务已启动! / All services started!$(NC)"
	@echo "$(BLUE)访问地址 / Access URLs:$(NC)"
	@echo "  - 前端 / Frontend: http://localhost:3000"
	@echo "  - API网关 / API Gateway: http://localhost:8000"
	@echo "  - 认证服务 / Auth Service: http://localhost:8001"
	@echo "  - 授权服务 / Authz Service: http://localhost:8002"
	@echo "  - Grafana监控 / Grafana: http://localhost:3001 (admin/grafana_admin_123)"
	@echo "  - Prometheus: http://localhost:9090"

start-dev: ## 启动开发环境 / Start development environment
	@echo "$(YELLOW)启动开发环境... / Starting development environment...$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)开发环境已启动! / Development environment started!$(NC)"

start-data: ## 仅启动数据层服务 / Start data layer services only
	@echo "$(YELLOW)启动数据层服务... / Starting data layer services...$(NC)"
	@docker-compose up -d postgres redis
	@echo "$(GREEN)数据层服务已启动! / Data layer services started!$(NC)"

stop: ## 停止所有服务 / Stop all services
	@echo "$(YELLOW)停止所有服务... / Stopping all services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)所有服务已停止! / All services stopped!$(NC)"

restart: ## 重启所有服务 / Restart all services
	@echo "$(YELLOW)重启所有服务... / Restarting all services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)所有服务已重启! / All services restarted!$(NC)"

restart-app: ## 重启应用服务（不包括数据库）/ Restart application services (exclude databases)
	@echo "$(YELLOW)重启应用服务... / Restarting application services...$(NC)"
	@docker-compose restart authentication-service authorization-service api-gateway frontend
	@echo "$(GREEN)应用服务已重启! / Application services restarted!$(NC)"

##@ 日志和监控 / Logs & Monitoring

logs: ## 查看所有服务日志 / View all services logs
	@docker-compose logs -f

logs-auth: ## 查看认证服务日志 / View authentication service logs
	@docker-compose logs -f authentication-service

logs-authz: ## 查看授权服务日志 / View authorization service logs
	@docker-compose logs -f authorization-service

logs-gateway: ## 查看网关日志 / View gateway logs
	@docker-compose logs -f api-gateway

logs-frontend: ## 查看前端日志 / View frontend logs
	@docker-compose logs -f frontend

ps: ## 查看服务状态 / View service status
	@docker-compose ps

top: ## 查看服务资源使用情况 / View service resource usage
	@docker stats $(shell docker-compose ps -q) --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"

##@ 健康检查 / Health Check

health: ## 检查所有服务健康状态 / Check all services health
	@echo "$(YELLOW)检查服务健康状态... / Checking services health...$(NC)"
	@echo "$(BLUE)数据库健康检查 / Database health check:$(NC)"
	@curl -s http://localhost:8001/health | jq '.checks.database' 2>/dev/null || echo "认证服务不可用 / Auth service unavailable"
	@echo "$(BLUE)Redis健康检查 / Redis health check:$(NC)"
	@curl -s http://localhost:8001/health | jq '.checks.redis' 2>/dev/null || echo "Redis不可用 / Redis unavailable"
	@echo "$(BLUE)认证服务健康检查 / Auth service health check:$(NC)"
	@curl -s http://localhost:8001/health | jq '.status' 2>/dev/null || echo "认证服务不可用 / Auth service unavailable"
	@echo "$(BLUE)授权服务健康检查 / Authz service health check:$(NC)"
	@curl -s http://localhost:8002/health | jq '.status' 2>/dev/null || echo "授权服务不可用 / Authz service unavailable"
	@echo "$(BLUE)网关健康检查 / Gateway health check:$(NC)"
	@curl -s http://localhost:8000/gateway/health | jq '.status' 2>/dev/null || echo "网关不可用 / Gateway unavailable"
	@echo "$(BLUE)前端健康检查 / Frontend health check:$(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200" && echo "前端正常 / Frontend OK" || echo "前端不可用 / Frontend unavailable"

ping-services: ## 测试所有服务连接 / Test all services connectivity
	@echo "$(YELLOW)测试服务连接... / Testing services connectivity...$(NC)"
	@for service in postgres redis authentication-service authorization-service api-gateway frontend; do \
		echo "$(BLUE)测试 $$service... / Testing $$service...$(NC)"; \
		docker-compose exec $$service echo "$$service is reachable" 2>/dev/null || echo "$(RED)$$service 不可达 / $$service is not reachable$(NC)"; \
	done

##@ 数据库管理 / Database Management

migrate: ## 运行数据库迁移 / Run database migrations
	@echo "$(YELLOW)运行数据库迁移... / Running database migrations...$(NC)"
	@docker-compose exec postgres psql -U iam_user -d iam_service -f /docker-entrypoint-initdb.d/01-init.sql
	@echo "$(GREEN)数据库迁移完成! / Database migrations completed!$(NC)"

seed: ## 加载种子数据 / Load seed data
	@echo "$(YELLOW)加载种子数据... / Loading seed data...$(NC)"
	@docker-compose exec postgres psql -U iam_user -d iam_service -f /docker-entrypoint-initdb.d/02-seeds.sql
	@echo "$(GREEN)种子数据加载完成! / Seed data loading completed!$(NC)"

db-shell: ## 连接到数据库Shell / Connect to database shell
	@docker-compose exec postgres psql -U iam_user -d iam_service

db-backup: ## 备份数据库 / Backup database
	@echo "$(YELLOW)备份数据库... / Backing up database...$(NC)"
	@mkdir -p ./backups
	@docker-compose exec -T postgres pg_dump -U iam_user -d iam_service > ./backups/iam_service_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)数据库备份完成! / Database backup completed!$(NC)"

db-restore: ## 恢复数据库 / Restore database
	@echo "$(YELLOW)恢复数据库... / Restoring database...$(NC)"
	@read -p "请输入备份文件名 / Please enter backup filename: " filename; \
	docker-compose exec -T postgres psql -U iam_user -d iam_service < ./backups/$$filename
	@echo "$(GREEN)数据库恢复完成! / Database restore completed!$(NC)"

##@ 测试 / Testing

test: ## 运行所有测试 / Run all tests
	@echo "$(YELLOW)运行所有测试... / Running all tests...$(NC)"
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@docker-compose -f docker-compose.test.yml down --volumes --remove-orphans

test-auth: ## 运行认证服务测试 / Run authentication service tests
	@echo "$(YELLOW)运行认证服务测试... / Running authentication service tests...$(NC)"
	@docker-compose exec authentication-service python -m pytest tests/ -v

test-authz: ## 运行授权服务测试 / Run authorization service tests
	@echo "$(YELLOW)运行授权服务测试... / Running authorization service tests...$(NC)"
	@docker-compose exec authorization-service python -m pytest tests/ -v

test-integration: ## 运行集成测试 / Run integration tests
	@echo "$(YELLOW)运行集成测试... / Running integration tests...$(NC)"
	@python tests/integration/run_integration_tests.py

##@ 代码质量 / Code Quality

lint: ## 运行代码检查 / Run code linting
	@echo "$(YELLOW)运行代码检查... / Running code linting...$(NC)"
	@docker-compose exec authentication-service flake8 src/
	@docker-compose exec authorization-service flake8 src/
	@docker-compose exec api-gateway flake8 src/
	@echo "$(GREEN)代码检查完成! / Code linting completed!$(NC)"

format: ## 格式化代码 / Format code
	@echo "$(YELLOW)格式化代码... / Formatting code...$(NC)"
	@docker-compose exec authentication-service black src/
	@docker-compose exec authorization-service black src/
	@docker-compose exec api-gateway black src/
	@echo "$(GREEN)代码格式化完成! / Code formatting completed!$(NC)"

##@ 清理 / Cleanup

clean: ## 清理未使用的Docker资源 / Clean unused Docker resources
	@echo "$(YELLOW)清理Docker资源... / Cleaning Docker resources...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)清理完成! / Cleanup completed!$(NC)"

clean-all: ## 清理所有Docker资源和数据 / Clean all Docker resources and data
	@echo "$(RED)警告: 这将删除所有数据! / Warning: This will delete all data!$(NC)"
	@read -p "确认继续? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker-compose down --volumes --remove-orphans
	@docker system prune -a -f --volumes
	@echo "$(GREEN)全部清理完成! / Complete cleanup finished!$(NC)"

reset: ## 重置服务和数据 / Reset services and data
	@echo "$(YELLOW)重置服务和数据... / Resetting services and data...$(NC)"
	@docker-compose down --volumes
	@docker-compose up -d
	@sleep 30
	@make migrate
	@make seed
	@echo "$(GREEN)服务重置完成! / Service reset completed!$(NC)"

##@ Docker Registry

docker-login: ## 登录Docker Registry / Login to Docker Registry
	@echo "$(YELLOW)登录Docker Registry... / Logging into Docker Registry...$(NC)"
	@docker login $(DOCKER_REGISTRY)

docker-build-all: ## 构建并标记所有镜像 / Build and tag all images
	@echo "$(YELLOW)构建并标记所有镜像... / Building and tagging all images...$(NC)"
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/auth-service:$(DOCKER_TAG) services/authentication-service/
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/authz-service:$(DOCKER_TAG) services/authorization-service/
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/gateway:$(DOCKER_TAG) services/api-gateway/
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/frontend:$(DOCKER_TAG) frontend/
	@echo "$(GREEN)镜像构建和标记完成! / Image build and tagging completed!$(NC)"

docker-push-all: ## 推送所有镜像到Registry / Push all images to registry
	@echo "$(YELLOW)推送所有镜像... / Pushing all images...$(NC)"
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/auth-service:$(DOCKER_TAG)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/authz-service:$(DOCKER_TAG)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/gateway:$(DOCKER_TAG)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/frontend:$(DOCKER_TAG)
	@echo "$(GREEN)镜像推送完成! / Image push completed!$(NC)"

##@ 部署 / Deployment

deploy-dev: ## 部署到开发环境 / Deploy to development environment
	@echo "$(YELLOW)部署到开发环境... / Deploying to development environment...$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
	@echo "$(GREEN)开发环境部署完成! / Development deployment completed!$(NC)"

deploy-staging: ## 部署到测试环境 / Deploy to staging environment
	@echo "$(YELLOW)部署到测试环境... / Deploying to staging environment...$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build
	@echo "$(GREEN)测试环境部署完成! / Staging deployment completed!$(NC)"

deploy-prod: ## 部署到生产环境 / Deploy to production environment
	@echo "$(RED)警告: 准备部署到生产环境! / Warning: About to deploy to production!$(NC)"
	@read -p "确认继续? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(YELLOW)部署到生产环境... / Deploying to production environment...$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "$(GREEN)生产环境部署完成! / Production deployment completed!$(NC)"

##@ 监控 / Monitoring

metrics: ## 查看服务指标 / View service metrics
	@echo "$(YELLOW)获取服务指标... / Fetching service metrics...$(NC)"
	@echo "$(BLUE)认证服务指标 / Auth service metrics:$(NC)"
	@curl -s http://localhost:9001/metrics | grep -E "^(http_requests_total|response_time_seconds)" | head -5 || echo "指标不可用 / Metrics unavailable"
	@echo "$(BLUE)授权服务指标 / Authz service metrics:$(NC)"
	@curl -s http://localhost:9002/metrics | grep -E "^(http_requests_total|response_time_seconds)" | head -5 || echo "指标不可用 / Metrics unavailable"
	@echo "$(BLUE)网关指标 / Gateway metrics:$(NC)"
	@curl -s http://localhost:9000/metrics | grep -E "^(http_requests_total|response_time_seconds)" | head -5 || echo "指标不可用 / Metrics unavailable"

dashboard: ## 打开监控仪表板 / Open monitoring dashboard
	@echo "$(BLUE)打开监控仪表板... / Opening monitoring dashboard...$(NC)"
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:3001; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3001; \
	fi

##@ 文档 / Documentation

docs: ## 生成API文档 / Generate API documentation
	@echo "$(YELLOW)生成API文档... / Generating API documentation...$(NC)"
	@echo "API文档地址 / API documentation URLs:"
	@echo "  - 认证服务 / Auth Service: http://localhost:8001/docs"
	@echo "  - 授权服务 / Authz Service: http://localhost:8002/docs"  
	@echo "  - API网关 / API Gateway: http://localhost:8000/docs"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8000/docs; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000/docs; \
	fi

##@ 工具 / Utilities

shell-auth: ## 进入认证服务容器 / Enter authentication service container
	@docker-compose exec authentication-service /bin/bash

shell-authz: ## 进入授权服务容器 / Enter authorization service container
	@docker-compose exec authorization-service /bin/bash

shell-gateway: ## 进入网关容器 / Enter gateway container
	@docker-compose exec api-gateway /bin/bash

shell-db: ## 进入数据库容器 / Enter database container
	@docker-compose exec postgres /bin/bash

shell-redis: ## 进入Redis容器 / Enter Redis container
	@docker-compose exec redis /bin/sh

env-check: ## 检查环境配置 / Check environment configuration
	@echo "$(YELLOW)检查环境配置... / Checking environment configuration...$(NC)"
	@if [ -f $(ENV_FILE) ]; then \
		echo "$(GREEN)✓ .env 文件存在 / .env file exists$(NC)"; \
	else \
		echo "$(RED)✗ .env 文件不存在，请运行 make init / .env file does not exist, run make init$(NC)"; \
	fi
	@echo "$(BLUE)Docker版本 / Docker version:$(NC)"
	@docker --version
	@echo "$(BLUE)Docker Compose版本 / Docker Compose version:$(NC)"
	@docker-compose --version
	@echo "$(BLUE)系统信息 / System information:$(NC)"
	@echo "  - OS: $(shell uname -s)"
	@echo "  - 架构 / Architecture: $(shell uname -m)"
	@echo "  - 可用内存 / Available memory: $(shell free -h 2>/dev/null | awk '/^Mem:/{print $$7}' || echo 'N/A')"
	@echo "  - 可用磁盘空间 / Available disk space: $(shell df -h . | awk 'NR==2{print $$4}')"

version: ## 显示版本信息 / Show version information
	@echo "$(CYAN)独立IAM认证授权服务 / Independent IAM Auth Service$(NC)"
	@echo "$(BLUE)版本 / Version: $(VERSION)$(NC)"
	@echo "$(BLUE)构建时间 / Build time: $(BUILD_TIME)$(NC)"
	@echo "$(BLUE)Git提交 / Git commit: $(GIT_COMMIT)$(NC)"

##@ 快速命令 / Quick Commands

dev: init start-dev ## 快速启动开发环境 / Quick start development environment

prod-deploy: build deploy-prod ## 快速生产部署 / Quick production deployment

full-reset: clean-all init start migrate seed ## 完全重置和重新开始 / Complete reset and restart

status: ps health ## 查看状态总览 / View status overview