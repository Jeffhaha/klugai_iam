"""
独立授权服务主程序
Authorization Service - 完全独立的授权微服务

这是一个完全独立的授权服务，提供：
- RBAC/ABAC授权
- 策略引擎
- 权限检查
- 审计日志
- 批量授权
"""

import asyncio
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加共享模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from src.models.authz_models import *
from src.services.policy_service import PolicyService
from src.services.authorization_engine import AuthorizationEngine
from src.services.audit_service import AuditService
from src.config.service_config import load_service_config
from src.database.database import DatabaseManager
from src.utils.logger import setup_logging

logger = structlog.get_logger(__name__)


class AuthorizationServiceApp:
    """独立授权服务应用"""
    
    def __init__(self):
        self.config = load_service_config("authorization")
        self.db_manager = DatabaseManager(self.config.database)
        self.policy_service: Optional[PolicyService] = None
        self.authorization_engine: Optional[AuthorizationEngine] = None
        self.audit_service: Optional[AuditService] = None
        
    async def initialize(self):
        """初始化服务"""
        logger.info("🚀 Initializing Authorization Service...")
        
        # 初始化数据库
        await self.db_manager.initialize()
        
        # 初始化服务组件
        self.policy_service = PolicyService(self.db_manager, self.config)
        self.audit_service = AuditService(self.db_manager, self.config)
        self.authorization_engine = AuthorizationEngine(
            policy_service=self.policy_service,
            audit_service=self.audit_service,
            config=self.config
        )
        
        # 初始化各个服务
        await self.policy_service.initialize()
        await self.audit_service.initialize()
        await self.authorization_engine.initialize()
        
        logger.info("✅ Authorization Service initialized successfully")
        
    async def shutdown(self):
        """关闭服务"""
        logger.info("🛑 Shutting down Authorization Service...")
        
        if self.authorization_engine:
            await self.authorization_engine.shutdown()
        if self.audit_service:
            await self.audit_service.shutdown()
        if self.policy_service:
            await self.policy_service.shutdown()
        if self.db_manager:
            await self.db_manager.close()
            
        logger.info("✅ Authorization Service shutdown completed")


# 全局应用实例
authz_app = AuthorizationServiceApp()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        await authz_app.initialize()
        yield
    finally:
        await authz_app.shutdown()


# 创建FastAPI应用
app = FastAPI(
    title="Authorization Service",
    description="独立的授权微服务",
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


# ============================================================================
# 授权API端点
# ============================================================================

@app.post("/authorize", response_model=AuthorizationResponse)
async def authorize(request: AuthorizationRequest):
    """单个授权检查"""
    try:
        logger.debug("Authorization request received", 
                    user_id=request.user_id, 
                    resource_id=request.resource_id, 
                    action=request.action)
        
        # 执行授权检查
        result = await authz_app.authorization_engine.authorize(request)
        
        logger.debug("Authorization result", 
                    user_id=request.user_id,
                    resource_id=request.resource_id,
                    action=request.action,
                    decision=result.decision.effect)
        
        return result
        
    except Exception as e:
        logger.error("Authorization failed", 
                    user_id=request.user_id,
                    resource_id=request.resource_id, 
                    error=str(e))
        
        # 返回拒绝决策
        return AuthorizationResponse(
            success=False,
            decision=AuthorizationDecision(
                effect=PolicyEffect.DENY,
                reason=f"Authorization error: {str(e)}",
                attributes_used=[],
                evaluation_time_ms=0,
                cache_hit=False,
                obligations=[],
                advice=["Check system logs for details"],
                timestamp=datetime.utcnow().isoformat()
            ),
            request_id=request.request_id
        )


@app.post("/authorize/bulk", response_model=BulkAuthorizationResponse)
async def authorize_bulk(request: BulkAuthorizationRequest):
    """批量授权检查"""
    try:
        logger.debug("Bulk authorization request received", 
                    user_id=request.user_id, 
                    request_count=len(request.requests))
        
        # 执行批量授权检查
        results = await authz_app.authorization_engine.authorize_bulk(request)
        
        # 统计结果
        permitted = sum(1 for r in results if r.decision.effect == PolicyEffect.PERMIT)
        denied = sum(1 for r in results if r.decision.effect == PolicyEffect.DENY)
        errors = sum(1 for r in results if r.decision.effect == PolicyEffect.INDETERMINATE)
        
        logger.debug("Bulk authorization completed", 
                    user_id=request.user_id,
                    total=len(results),
                    permitted=permitted,
                    denied=denied,
                    errors=errors)
        
        return BulkAuthorizationResponse(
            results=results,
            summary={
                "total": len(results),
                "permitted": permitted,
                "denied": denied,
                "errors": errors
            }
        )
        
    except Exception as e:
        logger.error("Bulk authorization failed", 
                    user_id=request.user_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Bulk authorization failed: {str(e)}")


@app.post("/authorize/batch-optimized", response_model=BulkAuthorizationResponse)
async def authorize_batch_optimized(request: BulkAuthorizationRequest):
    """批量优化授权检查"""
    try:
        logger.debug("Batch optimized authorization request received", 
                    user_id=request.user_id, 
                    request_count=len(request.requests))
        
        # 执行批量优化授权检查
        results = await authz_app.authorization_engine.authorize_batch_optimized(request)
        
        # 统计结果
        permitted = sum(1 for r in results if r.decision.effect == PolicyEffect.PERMIT)
        denied = sum(1 for r in results if r.decision.effect == PolicyEffect.DENY)
        errors = sum(1 for r in results if r.decision.effect == PolicyEffect.INDETERMINATE)
        
        return BulkAuthorizationResponse(
            results=results,
            summary={
                "total": len(results),
                "permitted": permitted,
                "denied": denied,
                "errors": errors
            }
        )
        
    except Exception as e:
        logger.error("Batch optimized authorization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch authorization failed: {str(e)}")


# ============================================================================
# 策略管理API端点
# ============================================================================

@app.get("/policies", response_model=dict)
async def list_policies(active_only: bool = True):
    """列出所有策略"""
    try:
        policies = await authz_app.policy_service.list_policies(active_only=active_only)
        return {"policies": policies}
        
    except Exception as e:
        logger.error("List policies failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list policies: {str(e)}")


@app.get("/policies/{policy_id}", response_model=PolicyModel)
async def get_policy(policy_id: str):
    """获取指定策略"""
    try:
        policy = await authz_app.policy_service.get_policy(policy_id)
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get policy failed", policy_id=policy_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")


@app.post("/policies", response_model=dict)
async def create_policy(request: dict):
    """创建新策略"""
    try:
        policy_data = request.get("policy")
        validate_syntax = request.get("validate_syntax", True)
        dry_run = request.get("dry_run", False)
        
        if not policy_data:
            raise HTTPException(status_code=400, detail="Policy data is required")
        
        # 创建策略
        policy_id = await authz_app.policy_service.create_policy(
            policy_data, validate_syntax=validate_syntax, dry_run=dry_run
        )
        
        if not policy_id:
            raise HTTPException(status_code=400, detail="Failed to create policy")
        
        logger.info("Policy created successfully", policy_id=policy_id)
        
        return {
            "message": "Policy created successfully",
            "policy_id": policy_id,
            "dry_run": dry_run
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Create policy failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@app.put("/policies/{policy_id}", response_model=dict)
async def update_policy(policy_id: str, request: dict):
    """更新策略"""
    try:
        updates = request.get("updates", {})
        version_increment = request.get("version_increment", True)
        
        success = await authz_app.policy_service.update_policy(
            policy_id, updates, version_increment=version_increment
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Policy not found or update failed")
        
        logger.info("Policy updated successfully", policy_id=policy_id)
        
        return {"message": "Policy updated successfully", "policy_id": policy_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update policy failed", policy_id=policy_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")


@app.delete("/policies/{policy_id}", response_model=dict)
async def delete_policy(policy_id: str):
    """删除策略"""
    try:
        success = await authz_app.policy_service.delete_policy(policy_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        logger.info("Policy deleted successfully", policy_id=policy_id)
        
        return {"message": "Policy deleted successfully", "policy_id": policy_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete policy failed", policy_id=policy_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")


# ============================================================================
# 审计和监控API端点
# ============================================================================

@app.get("/audit/decisions", response_model=dict)
async def query_audit_log(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    action: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """查询审计决策日志"""
    try:
        filters = {}
        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time
        if user_id:
            filters["user_id"] = user_id
        if resource_id:
            filters["resource_id"] = resource_id
        if action:
            filters["action"] = action
        if decision:
            filters["decision"] = decision
        
        filters["limit"] = limit
        filters["offset"] = offset
        
        decisions = await authz_app.audit_service.query_decisions(filters)
        
        return {
            "decisions": decisions,
            "total": len(decisions),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Query audit log failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to query audit log: {str(e)}")


@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    try:
        status = await authz_app.authorization_engine.get_system_status()
        return status
        
    except Exception as e:
        logger.error("Get system status failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@app.get("/metrics/performance", response_model=dict)
async def get_performance_metrics():
    """获取性能指标"""
    try:
        metrics = await authz_app.authorization_engine.get_performance_metrics()
        return metrics
        
    except Exception as e:
        logger.error("Get performance metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# ============================================================================
# 管理API端点
# ============================================================================

@app.post("/admin/cache/clear", response_model=dict)
async def clear_cache():
    """清空缓存"""
    try:
        success = await authz_app.authorization_engine.clear_cache()
        
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Clear cache failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.post("/admin/warm-cache", response_model=dict)
async def warm_cache():
    """预热缓存"""
    try:
        success = await authz_app.authorization_engine.warm_cache()
        
        if success:
            return {"message": "Cache warmed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to warm cache")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Warm cache failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@app.get("/admin/config", response_model=dict)
async def get_service_config():
    """获取服务配置"""
    try:
        config = {
            "service_name": "authorization-service",
            "version": "1.0.0",
            "cache_enabled": authz_app.config.cache.enabled,
            "cache_ttl": authz_app.config.cache.ttl_seconds,
            "audit_enabled": authz_app.config.audit.enabled,
            "default_policy_effect": authz_app.config.policies.default_effect
        }
        
        return config
        
    except Exception as e:
        logger.error("Get service config failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@app.get("/admin/security-alerts", response_model=dict)
async def get_security_alerts(threat_level: Optional[str] = None, limit: int = 50):
    """获取安全告警"""
    try:
        alerts = await authz_app.audit_service.get_security_alerts(
            threat_level=threat_level, limit=limit
        )
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "limit": limit
        }
        
    except Exception as e:
        logger.error("Get security alerts failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@app.post("/admin/security-alert/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_security_alert(alert_id: str):
    """确认安全告警"""
    try:
        success = await authz_app.audit_service.acknowledge_alert(alert_id)
        
        if success:
            return {"message": "Alert acknowledged successfully", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Acknowledge alert failed", alert_id=alert_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


# ============================================================================
# 健康检查和监控端点
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查各个组件的健康状态
        db_healthy = await authz_app.db_manager.health_check()
        policy_healthy = await authz_app.policy_service.health_check() if authz_app.policy_service else False
        engine_healthy = await authz_app.authorization_engine.health_check() if authz_app.authorization_engine else False
        
        status = "healthy" if (db_healthy and policy_healthy and engine_healthy) else "unhealthy"
        
        return {
            "status": status,
            "service": "authorization-service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "policy_service": "healthy" if policy_healthy else "unhealthy",
                "authorization_engine": "healthy" if engine_healthy else "unhealthy"
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "authorization-service",
                "error": str(e)
            }
        )


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
    setup_logging("authorization-service")
    
    # 获取配置
    host = os.getenv("AUTHZ_HOST", "0.0.0.0")
    port = int(os.getenv("AUTHZ_PORT", "8002"))
    workers = int(os.getenv("AUTHZ_WORKERS", "1"))
    reload = os.getenv("AUTHZ_RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Authorization Service on {host}:{port}")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info"
    )