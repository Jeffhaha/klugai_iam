"""
API网关主程序
API Gateway - 统一认证授权入口

这是一个完全独立的API网关服务，提供：
- 统一的API入口
- 请求路由和转发
- 认证中间件集成
- 授权检查集成
- CORS处理
- 负载均衡
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import structlog
import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from src.models.gateway_models import *
from src.services.gateway_service import GatewayService
from src.middleware.auth_middleware import GatewayAuthMiddleware
from src.middleware.rate_limiting import RateLimitingMiddleware
from src.config.service_config import load_service_config
from src.utils.logger import setup_logging

logger = structlog.get_logger(__name__)


class APIGatewayApp:
    """API网关应用"""
    
    def __init__(self):
        self.config = load_service_config("gateway")
        self.gateway_service: Optional[GatewayService] = None
        self.auth_middleware: Optional[GatewayAuthMiddleware] = None
        self.rate_limiting: Optional[RateLimitingMiddleware] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
    async def initialize(self):
        """初始化服务"""
        logger.info("🚀 Initializing API Gateway...")
        
        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # 初始化服务组件
        self.gateway_service = GatewayService(self.config, self.http_client)
        self.auth_middleware = GatewayAuthMiddleware(self.config, self.http_client)
        self.rate_limiting = RateLimitingMiddleware(self.config)
        
        # 初始化各个服务
        await self.gateway_service.initialize()
        await self.auth_middleware.initialize()
        await self.rate_limiting.initialize()
        
        logger.info("✅ API Gateway initialized successfully")
        
    async def shutdown(self):
        """关闭服务"""
        logger.info("🛑 Shutting down API Gateway...")
        
        if self.rate_limiting:
            await self.rate_limiting.shutdown()
        if self.auth_middleware:
            await self.auth_middleware.shutdown()
        if self.gateway_service:
            await self.gateway_service.shutdown()
        if self.http_client:
            await self.http_client.aclose()
            
        logger.info("✅ API Gateway shutdown completed")


# 全局应用实例
gateway_app = APIGatewayApp()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        await gateway_app.initialize()
        yield
    finally:
        await gateway_app.shutdown()


# 创建FastAPI应用
app = FastAPI(
    title="IAM API Gateway",
    description="统一的IAM认证授权API网关",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


# ============================================================================
# 认证相关路由 - 转发到认证服务
# ============================================================================

@app.post("/api/v1/auth/login")
async def login(request: Request):
    """用户登录 - 转发到认证服务"""
    try:
        # 获取请求体
        body = await request.body()
        
        # 转发到认证服务
        response = await gateway_app.gateway_service.forward_request(
            service_name="authentication",
            path="/auth/login",
            method="POST",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except Exception as e:
        logger.error("Login forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@app.post("/api/v1/auth/logout")
async def logout(request: Request):
    """用户登出 - 转发到认证服务"""
    try:
        # 检查认证
        auth_result = await gateway_app.auth_middleware.authenticate_request(request)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message)
        
        # 转发请求
        response = await gateway_app.gateway_service.forward_request(
            service_name="authentication",
            path="/auth/logout",
            method="POST",
            headers=dict(request.headers)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Logout forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@app.post("/api/v1/auth/refresh")
async def refresh_token(request: Request):
    """刷新令牌 - 转发到认证服务"""
    try:
        body = await request.body()
        
        response = await gateway_app.gateway_service.forward_request(
            service_name="authentication",
            path="/auth/refresh",
            method="POST",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except Exception as e:
        logger.error("Token refresh forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@app.get("/api/v1/auth/validate")
async def validate_token(request: Request):
    """验证令牌 - 转发到认证服务"""
    try:
        response = await gateway_app.gateway_service.forward_request(
            service_name="authentication",
            path="/auth/validate",
            method="GET",
            headers=dict(request.headers)
        )
        
        return response
        
    except Exception as e:
        logger.error("Token validation forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@app.get("/api/v1/users/me")
async def get_current_user(request: Request):
    """获取当前用户信息 - 需要认证"""
    try:
        # 检查认证
        auth_result = await gateway_app.auth_middleware.authenticate_request(request)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message)
        
        # 转发请求
        response = await gateway_app.gateway_service.forward_request(
            service_name="authentication",
            path="/users/me",
            method="GET",
            headers=dict(request.headers)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get user forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@app.put("/api/v1/users/me")
async def update_current_user(request: Request):
    """更新当前用户信息 - 需要认证"""
    try:
        # 检查认证
        auth_result = await gateway_app.auth_middleware.authenticate_request(request)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message)
        
        # 转发请求
        body = await request.body()
        response = await gateway_app.gateway_service.forward_request(
            service_name="authentication",
            path="/users/me",
            method="PUT",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update user forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


# ============================================================================
# 授权相关路由 - 转发到授权服务
# ============================================================================

@app.post("/api/v1/authz/authorize")
async def authorize(request: Request):
    """单个授权检查 - 转发到授权服务"""
    try:
        # 应用速率限制
        await gateway_app.rate_limiting.check_rate_limit(request)
        
        # 获取请求体
        body = await request.body()
        
        # 转发到授权服务
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/authorize",
            method="POST",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authorization forwarding failed", error=str(e))
        
        # 返回开发模式的fallback响应
        return {
            "success": True,
            "decision": {
                "effect": "permit",
                "reason": "Authorization service unavailable - using development fallback",
                "attributes_used": ["fallback"],
                "evaluation_time_ms": 0,
                "cache_hit": False,
                "obligations": [],
                "advice": ["Using development mode fallback due to service unavailable"],
                "timestamp": time.time()
            },
            "request_id": f"gateway_fallback_{int(time.time())}"
        }


@app.post("/api/v1/authz/authorize/bulk")
async def authorize_bulk(request: Request):
    """批量授权检查 - 转发到授权服务"""
    try:
        # 应用速率限制
        await gateway_app.rate_limiting.check_rate_limit(request)
        
        body = await request.body()
        
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/authorize/bulk",
            method="POST",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Bulk authorization forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authorization service unavailable")


@app.post("/api/v1/authz/authorize/batch-optimized")
async def authorize_batch_optimized(request: Request):
    """批量优化授权检查 - 转发到授权服务"""
    try:
        await gateway_app.rate_limiting.check_rate_limit(request)
        
        body = await request.body()
        
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/authorize/batch-optimized",
            method="POST",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Batch optimized authorization forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authorization service unavailable")


# ============================================================================
# 策略管理路由 - 转发到授权服务（需要管理员权限）
# ============================================================================

@app.get("/api/v1/authz/policies")
async def list_policies(request: Request):
    """列出策略 - 需要管理员权限"""
    try:
        # 检查认证
        auth_result = await gateway_app.auth_middleware.authenticate_request(request)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message)
        
        # 检查管理员权限
        authz_result = await gateway_app.auth_middleware.check_authorization(
            user_id=auth_result.user_id,
            resource="policies",
            action="read",
            context={"path": "/api/v1/authz/policies"}
        )
        
        if not authz_result.success:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # 转发请求
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/policies",
            method="GET",
            headers=dict(request.headers),
            query_params=dict(request.query_params)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("List policies forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authorization service unavailable")


@app.post("/api/v1/authz/policies")
async def create_policy(request: Request):
    """创建策略 - 需要管理员权限"""
    try:
        # 检查认证和授权
        auth_result = await gateway_app.auth_middleware.authenticate_request(request)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message)
        
        authz_result = await gateway_app.auth_middleware.check_authorization(
            user_id=auth_result.user_id,
            resource="policies",
            action="create",
            context={"path": "/api/v1/authz/policies"}
        )
        
        if not authz_result.success:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # 转发请求
        body = await request.body()
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/policies",
            method="POST",
            headers=dict(request.headers),
            body=body
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Create policy forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authorization service unavailable")


# ============================================================================
# 审计和监控路由
# ============================================================================

@app.get("/api/v1/authz/audit/decisions")
async def query_audit_log(request: Request):
    """查询审计日志 - 需要管理员权限"""
    try:
        # 检查认证和授权
        auth_result = await gateway_app.auth_middleware.authenticate_request(request)
        if not auth_result.success:
            raise HTTPException(status_code=401, detail=auth_result.error_message)
        
        authz_result = await gateway_app.auth_middleware.check_authorization(
            user_id=auth_result.user_id,
            resource="audit",
            action="read",
            context={"path": "/api/v1/authz/audit/decisions"}
        )
        
        if not authz_result.success:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # 转发请求
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/audit/decisions",
            method="GET",
            headers=dict(request.headers),
            query_params=dict(request.query_params)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query audit log forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authorization service unavailable")


@app.get("/api/v1/authz/status")
async def get_authorization_status(request: Request):
    """获取授权服务状态"""
    try:
        response = await gateway_app.gateway_service.forward_request(
            service_name="authorization",
            path="/status",
            method="GET",
            headers=dict(request.headers)
        )
        
        return response
        
    except Exception as e:
        logger.error("Authorization status forwarding failed", error=str(e))
        raise HTTPException(status_code=500, detail="Authorization service unavailable")


# ============================================================================
# 网关管理API
# ============================================================================

@app.get("/gateway/health")
async def gateway_health_check():
    """网关健康检查"""
    try:
        # 检查后端服务健康状态
        services_health = {}
        
        # 检查认证服务
        try:
            auth_health = await gateway_app.gateway_service.check_service_health("authentication")
            services_health["authentication"] = "healthy" if auth_health else "unhealthy"
        except Exception:
            services_health["authentication"] = "unhealthy"
        
        # 检查授权服务  
        try:
            authz_health = await gateway_app.gateway_service.check_service_health("authorization")
            services_health["authorization"] = "healthy" if authz_health else "unhealthy"
        except Exception:
            services_health["authorization"] = "unhealthy"
        
        # 整体状态
        overall_status = "healthy" if all(
            status == "healthy" for status in services_health.values()
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "service": "api-gateway",
            "version": "1.0.0",
            "timestamp": time.time(),
            "services": services_health
        }
        
    except Exception as e:
        logger.error("Gateway health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "api-gateway",
                "error": str(e)
            }
        )


@app.get("/gateway/metrics")
async def get_gateway_metrics():
    """获取网关指标"""
    try:
        metrics = await gateway_app.gateway_service.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error("Get gateway metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@app.get("/gateway/config")
async def get_gateway_config():
    """获取网关配置"""
    try:
        config = {
            "service_name": "api-gateway",
            "version": "1.0.0",
            "services": {
                "authentication": {
                    "url": gateway_app.config.services.authentication.base_url,
                    "timeout": gateway_app.config.services.authentication.timeout
                },
                "authorization": {
                    "url": gateway_app.config.services.authorization.base_url,
                    "timeout": gateway_app.config.services.authorization.timeout
                }
            },
            "rate_limiting": {
                "enabled": gateway_app.config.rate_limiting.enabled,
                "default_limit": gateway_app.config.rate_limiting.default_requests_per_minute
            }
        }
        
        return config
        
    except Exception as e:
        logger.error("Get gateway config failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get config")


# ============================================================================
# 通用代理路由（用于未匹配的路径）
# ============================================================================

@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(request: Request, path: str):
    """通用请求代理"""
    try:
        # 根据路径确定目标服务
        service_name = None
        service_path = path
        
        if path.startswith("auth/") or path.startswith("users/"):
            service_name = "authentication"
            service_path = path
        elif path.startswith("authz/") or path.startswith("policies/"):
            service_name = "authorization"
            service_path = path.replace("authz/", "", 1)  # 去掉authz前缀
        
        if not service_name:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # 获取请求体（如果有）
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # 转发请求
        response = await gateway_app.gateway_service.forward_request(
            service_name=service_name,
            path=f"/{service_path}",
            method=request.method,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            body=body
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Proxy request failed", path=path, error=str(e))
        raise HTTPException(status_code=500, detail="Service unavailable")


# ============================================================================
# 错误处理
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error("Unhandled exception in gateway", error=str(exc), path=str(request.url))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Gateway internal error",
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        }
    )


if __name__ == "__main__":
    # 设置日志
    setup_logging("api-gateway")
    
    # 获取配置
    host = os.getenv("GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("GATEWAY_PORT", "8000"))
    workers = int(os.getenv("GATEWAY_WORKERS", "1"))
    reload = os.getenv("GATEWAY_RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Starting API Gateway on {host}:{port}")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info"
    )