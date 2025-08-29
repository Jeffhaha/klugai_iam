"""
独立认证服务主程序
Authentication Service - 完全独立的认证微服务

这是一个完全独立的认证服务，提供：
- JWT Token认证
- 用户管理
- 会话管理
- 密码策略
- 多因子认证
"""

import asyncio
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from src.models.auth_models import *
from src.services.user_service import UserService
from src.services.token_service import TokenService
from src.services.session_service import SessionService
from src.middleware.auth_middleware import AuthenticationMiddleware
from src.config.service_config import load_service_config
from src.database.database import DatabaseManager
from src.utils.logger import setup_logging

logger = structlog.get_logger(__name__)


class AuthenticationServiceApp:
    """独立认证服务应用"""
    
    def __init__(self):
        self.config = load_service_config("authentication")
        self.db_manager = DatabaseManager(self.config.database)
        self.user_service: Optional[UserService] = None
        self.token_service: Optional[TokenService] = None
        self.session_service: Optional[SessionService] = None
        self.auth_middleware: Optional[AuthenticationMiddleware] = None
        
    async def initialize(self):
        """初始化服务"""
        logger.info("🚀 Initializing Authentication Service...")
        
        # 初始化数据库
        await self.db_manager.initialize()
        
        # 初始化服务组件
        self.user_service = UserService(self.db_manager, self.config)
        self.token_service = TokenService(self.config.jwt)
        self.session_service = SessionService(self.db_manager, self.config)
        self.auth_middleware = AuthenticationMiddleware(
            user_service=self.user_service,
            token_service=self.token_service,
            session_service=self.session_service
        )
        
        # 初始化各个服务
        await self.user_service.initialize()
        await self.session_service.initialize()
        
        logger.info("✅ Authentication Service initialized successfully")
        
    async def shutdown(self):
        """关闭服务"""
        logger.info("🛑 Shutting down Authentication Service...")
        
        if self.session_service:
            await self.session_service.shutdown()
        if self.user_service:
            await self.user_service.shutdown()
        if self.db_manager:
            await self.db_manager.close()
            
        logger.info("✅ Authentication Service shutdown completed")


# 全局应用实例
auth_app = AuthenticationServiceApp()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        await auth_app.initialize()
        yield
    finally:
        await auth_app.shutdown()


# 创建FastAPI应用
app = FastAPI(
    title="Authentication Service",
    description="独立的认证微服务",
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


# 依赖注入函数
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserProfile]:
    """获取当前用户"""
    if not credentials:
        return None
        
    try:
        user = await auth_app.auth_middleware.authenticate_jwt(credentials.credentials)
        return user
    except Exception as e:
        logger.warning("Token authentication failed", error=str(e))
        return None


async def require_authentication(
    current_user: Optional[UserProfile] = Depends(get_current_user)
) -> UserProfile:
    """需要认证的依赖"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user


# ============================================================================
# 认证API端点
# ============================================================================

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    try:
        # 验证用户凭据
        user = await auth_app.user_service.authenticate_user(
            request.username, request.password
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")
        
        if user.is_locked:
            raise HTTPException(status_code=423, detail="Account is locked")
        
        # 生成JWT Token
        access_token = await auth_app.token_service.create_access_token(user)
        refresh_token = await auth_app.token_service.create_refresh_token(user)
        
        # 创建会话
        session = await auth_app.session_service.create_session(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        # 更新用户最后登录时间
        await auth_app.user_service.update_last_login(user.id)
        
        logger.info("User logged in successfully", user_id=user.id, username=user.username)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=auth_app.config.jwt.expiration_minutes * 60,
            user=user,
            session_id=session.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/auth/logout")
async def logout(
    current_user: UserProfile = Depends(require_authentication),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """用户登出"""
    try:
        # 撤销当前token
        await auth_app.token_service.revoke_token(credentials.credentials)
        
        # 清除会话
        await auth_app.session_service.end_session_by_user(current_user.id)
        
        logger.info("User logged out successfully", user_id=current_user.id)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(status_code=500, detail="Logout failed")


@app.post("/auth/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        user = await auth_app.token_service.validate_refresh_token(request.refresh_token)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # 生成新的访问令牌
        new_access_token = await auth_app.token_service.create_access_token(user)
        
        # 可选：生成新的刷新令牌
        new_refresh_token = None
        if auth_app.config.jwt.enable_refresh:
            new_refresh_token = await auth_app.token_service.create_refresh_token(user)
            # 撤销旧的刷新令牌
            await auth_app.token_service.revoke_token(request.refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": auth_app.config.jwt.expiration_minutes * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(status_code=500, detail="Token refresh failed")


@app.get("/auth/validate", response_model=TokenValidationResponse)
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """验证访问令牌"""
    try:
        if not credentials:
            return TokenValidationResponse(valid=False)
        
        # 验证令牌
        user = await auth_app.auth_middleware.authenticate_jwt(credentials.credentials)
        
        if not user:
            return TokenValidationResponse(valid=False)
        
        # 获取令牌信息
        token_info = await auth_app.token_service.decode_token(credentials.credentials)
        
        return TokenValidationResponse(
            valid=True,
            user_id=user.id,
            expires_at=datetime.fromtimestamp(token_info.get("exp", 0)).isoformat(),
            scopes=token_info.get("scopes", [])
        )
        
    except Exception as e:
        logger.warning("Token validation failed", error=str(e))
        return TokenValidationResponse(valid=False, error_message=str(e))


# ============================================================================
# 用户管理API端点
# ============================================================================

@app.get("/users/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserProfile = Depends(require_authentication)
):
    """获取当前用户信息"""
    return current_user


@app.put("/users/me", response_model=UserProfile)
async def update_current_user_profile(
    update_data: dict,
    current_user: UserProfile = Depends(require_authentication)
):
    """更新当前用户信息"""
    try:
        updated_user = await auth_app.user_service.update_user(
            current_user.id, update_data
        )
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info("User profile updated", user_id=current_user.id)
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Profile update failed", error=str(e))
        raise HTTPException(status_code=500, detail="Profile update failed")


@app.post("/users/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: UserProfile = Depends(require_authentication)
):
    """修改密码"""
    try:
        # 验证当前密码
        is_valid = await auth_app.user_service.verify_password(
            current_user.id, request.current_password
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # 更新密码
        success = await auth_app.user_service.change_password(
            current_user.id, request.new_password
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Password change failed")
        
        # 撤销所有现有的token（强制重新登录）
        await auth_app.session_service.end_all_user_sessions(current_user.id)
        
        logger.info("Password changed successfully", user_id=current_user.id)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e))
        raise HTTPException(status_code=500, detail="Password change failed")


# ============================================================================
# 会话管理API端点
# ============================================================================

@app.get("/sessions/me")
async def get_current_sessions(
    current_user: UserProfile = Depends(require_authentication)
):
    """获取当前用户的所有会话"""
    try:
        sessions = await auth_app.session_service.get_user_sessions(current_user.id)
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error("Get sessions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get sessions")


@app.delete("/sessions/{session_id}")
async def end_session(
    session_id: str,
    current_user: UserProfile = Depends(require_authentication)
):
    """结束指定会话"""
    try:
        success = await auth_app.session_service.end_session(
            session_id, current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("End session failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to end session")


@app.delete("/sessions/all")
async def end_all_sessions(
    current_user: UserProfile = Depends(require_authentication)
):
    """结束当前用户的所有会话"""
    try:
        count = await auth_app.session_service.end_all_user_sessions(current_user.id)
        return {"message": f"Ended {count} sessions successfully"}
        
    except Exception as e:
        logger.error("End all sessions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to end sessions")


# ============================================================================
# 健康检查和监控端点
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db_healthy = await auth_app.db_manager.health_check()
        
        # 检查Redis连接
        redis_healthy = await auth_app.session_service.health_check() if auth_app.session_service else False
        
        status = "healthy" if (db_healthy and redis_healthy) else "unhealthy"
        
        return {
            "status": status,
            "service": "authentication-service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy"
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "authentication-service",
                "error": str(e)
            }
        )


@app.get("/metrics")
async def get_metrics():
    """获取服务指标"""
    try:
        metrics = {}
        
        if auth_app.user_service:
            metrics["users"] = await auth_app.user_service.get_metrics()
        
        if auth_app.session_service:
            metrics["sessions"] = await auth_app.session_service.get_metrics()
        
        if auth_app.token_service:
            metrics["tokens"] = auth_app.token_service.get_metrics()
        
        return metrics
        
    except Exception as e:
        logger.error("Get metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")


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
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error("Unhandled exception", error=str(exc), path=str(request.url))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


if __name__ == "__main__":
    # 设置日志
    setup_logging("authentication-service")
    
    # 获取配置
    host = os.getenv("AUTH_HOST", "0.0.0.0")
    port = int(os.getenv("AUTH_PORT", "8001"))
    workers = int(os.getenv("AUTH_WORKERS", "1"))
    reload = os.getenv("AUTH_RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Authentication Service on {host}:{port}")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info"
    )