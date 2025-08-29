"""
用户服务 - 用户管理和认证的核心业务逻辑
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import structlog
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import UserModel, UserSessionModel, AuditLogModel
from ..config.service_config import AuthServiceConfig

logger = structlog.get_logger(__name__)


class UserService:
    """用户管理服务"""
    
    def __init__(self, db_manager, config: AuthServiceConfig):
        self.db_manager = db_manager
        self.config = config
        
        # 安全配置
        self.max_failed_attempts = config.security.max_failed_attempts
        self.lockout_duration = timedelta(minutes=config.security.lockout_duration_minutes)
        
        # 缓存
        self._user_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5分钟
        
        # 指标
        self.metrics = {
            "total_users": 0,
            "active_users": 0,
            "locked_users": 0,
            "failed_attempts_today": 0,
            "successful_logins_today": 0
        }
    
    async def initialize(self):
        """初始化用户服务"""
        logger.info("🚀 Initializing User Service...")
        
        # 创建默认管理员用户
        await self._create_default_admin()
        
        # 更新指标
        await self._update_metrics()
        
        logger.info("✅ User Service initialized successfully")
    
    async def shutdown(self):
        """关闭用户服务"""
        self._user_cache.clear()
        logger.info("✅ User Service shutdown completed")
    
    # ========================================================================
    # 用户认证方法
    # ========================================================================
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """认证用户"""
        try:
            # 获取用户
            user = await self.get_user_by_username(username)
            if not user:
                await self._log_auth_event(None, "login_failed", False, 
                                         metadata={"reason": "user_not_found", "username": username})
                return None
            
            # 检查账户状态
            if not user["is_active"]:
                await self._log_auth_event(user["id"], "login_failed", False, 
                                         metadata={"reason": "account_inactive"})
                return None
            
            # 检查账户是否被锁定
            if user["locked_until"] and user["locked_until"] > datetime.utcnow():
                await self._log_auth_event(user["id"], "login_failed", False, 
                                         metadata={"reason": "account_locked"})
                return None
            
            # 验证密码
            if not self._verify_password(password, user["password_hash"]):
                await self._handle_failed_login(user)
                await self._log_auth_event(user["id"], "login_failed", False, 
                                         metadata={"reason": "invalid_password"})
                return None
            
            # 登录成功，重置失败计数
            await self._reset_failed_attempts(user["id"])
            await self._update_last_login(user["id"])
            
            # 记录成功登录
            await self._log_auth_event(user["id"], "login_success", True)
            
            # 更新指标
            self.metrics["successful_logins_today"] += 1
            
            return user
            
        except Exception as e:
            logger.error("User authentication failed", username=username, error=str(e))
            return None
    
    async def verify_password(self, user_id: str, password: str) -> bool:
        """验证用户密码"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            return self._verify_password(password, user["password_hash"])
            
        except Exception as e:
            logger.error("Password verification failed", user_id=user_id, error=str(e))
            return False
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码哈希"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def _hash_password(self, password: str) -> str:
        """生成密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # ========================================================================
    # 用户管理方法
    # ========================================================================
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        try:
            # 检查缓存
            cache_key = f"user_id:{user_id}"
            if cache_key in self._user_cache:
                cached_data = self._user_cache[cache_key]
                if cached_data["expires"] > datetime.utcnow().timestamp():
                    return cached_data["user"]
            
            # 从数据库查询
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(UserModel).where(UserModel.id == user_id)
                )
                user_model = result.scalar_one_or_none()
                
                if not user_model:
                    return None
                
                user_data = {
                    "id": user_model.id,
                    "username": user_model.username,
                    "email": user_model.email,
                    "first_name": user_model.first_name,
                    "last_name": user_model.last_name,
                    "display_name": user_model.display_name or user_model.username,
                    "roles": user_model.roles or [],
                    "primary_role": user_model.primary_role,
                    "is_active": user_model.is_active,
                    "email_verified": user_model.email_verified,
                    "mfa_enabled": user_model.mfa_enabled,
                    "password_hash": user_model.password_hash,
                    "failed_login_attempts": user_model.failed_login_attempts,
                    "locked_until": user_model.locked_until,
                    "last_login": user_model.last_login,
                    "created_at": user_model.created_at.isoformat(),
                    "updated_at": user_model.updated_at.isoformat() if user_model.updated_at else None,
                    "metadata": user_model.metadata or {}
                }
                
                # 缓存用户数据
                self._user_cache[cache_key] = {
                    "user": user_data,
                    "expires": datetime.utcnow().timestamp() + self._cache_ttl
                }
                
                return user_data
                
        except Exception as e:
            logger.error("Get user by ID failed", user_id=user_id, error=str(e))
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        try:
            # 检查缓存
            cache_key = f"username:{username}"
            if cache_key in self._user_cache:
                cached_data = self._user_cache[cache_key]
                if cached_data["expires"] > datetime.utcnow().timestamp():
                    return cached_data["user"]
            
            # 从数据库查询
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(UserModel).where(UserModel.username == username)
                )
                user_model = result.scalar_one_or_none()
                
                if not user_model:
                    return None
                
                user_data = {
                    "id": user_model.id,
                    "username": user_model.username,
                    "email": user_model.email,
                    "first_name": user_model.first_name,
                    "last_name": user_model.last_name,
                    "display_name": user_model.display_name or user_model.username,
                    "roles": user_model.roles or [],
                    "primary_role": user_model.primary_role,
                    "is_active": user_model.is_active,
                    "email_verified": user_model.email_verified,
                    "mfa_enabled": user_model.mfa_enabled,
                    "password_hash": user_model.password_hash,
                    "failed_login_attempts": user_model.failed_login_attempts,
                    "locked_until": user_model.locked_until,
                    "last_login": user_model.last_login,
                    "created_at": user_model.created_at.isoformat(),
                    "updated_at": user_model.updated_at.isoformat() if user_model.updated_at else None,
                    "metadata": user_model.metadata or {}
                }
                
                # 缓存用户数据
                self._user_cache[cache_key] = {
                    "user": user_data,
                    "expires": datetime.utcnow().timestamp() + self._cache_ttl
                }
                
                return user_data
                
        except Exception as e:
            logger.error("Get user by username failed", username=username, error=str(e))
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """创建用户"""
        try:
            # 验证必需字段
            required_fields = ["username", "email", "password"]
            for field in required_fields:
                if field not in user_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # 检查用户名和邮箱是否已存在
            existing_user = await self.get_user_by_username(user_data["username"])
            if existing_user:
                raise ValueError("Username already exists")
            
            # 生成用户ID和密码哈希
            user_id = secrets.token_urlsafe(16)
            password_hash = self._hash_password(user_data["password"])
            
            async with self.db_manager.get_session() as session:
                user_model = UserModel(
                    id=user_id,
                    username=user_data["username"],
                    email=user_data["email"],
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    display_name=user_data.get("display_name"),
                    password_hash=password_hash,
                    roles=user_data.get("roles", ["user"]),
                    primary_role=user_data.get("primary_role", "user"),
                    is_active=user_data.get("is_active", True),
                    email_verified=user_data.get("email_verified", False),
                    mfa_enabled=user_data.get("mfa_enabled", False),
                    metadata=user_data.get("metadata", {}),
                    created_at=datetime.utcnow()
                )
                
                session.add(user_model)
                await session.commit()
                
                logger.info("User created successfully", user_id=user_id, username=user_data["username"])
                
                # 记录审计日志
                await self._log_auth_event(user_id, "user_created", True, 
                                         metadata={"username": user_data["username"]})
                
                # 更新指标
                self.metrics["total_users"] += 1
                if user_data.get("is_active", True):
                    self.metrics["active_users"] += 1
                
                return user_id
                
        except Exception as e:
            logger.error("User creation failed", error=str(e))
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新用户信息"""
        try:
            async with self.db_manager.get_session() as session:
                # 构建更新语句
                update_fields = {}
                
                allowed_fields = [
                    "first_name", "last_name", "display_name", "email", 
                    "roles", "primary_role", "is_active", "email_verified", 
                    "mfa_enabled", "metadata"
                ]
                
                for field in allowed_fields:
                    if field in update_data:
                        update_fields[field] = update_data[field]
                
                if update_fields:
                    update_fields["updated_at"] = datetime.utcnow()
                    
                    result = await session.execute(
                        update(UserModel)
                        .where(UserModel.id == user_id)
                        .values(**update_fields)
                        .returning(UserModel)
                    )
                    
                    updated_user = result.scalar_one_or_none()
                    
                    if updated_user:
                        await session.commit()
                        
                        # 清除缓存
                        self._invalidate_user_cache(user_id)
                        
                        logger.info("User updated successfully", user_id=user_id)
                        
                        # 记录审计日志
                        await self._log_auth_event(user_id, "user_updated", True, 
                                                 metadata={"fields": list(update_fields.keys())})
                        
                        return await self.get_user_by_id(user_id)
                    
                return None
                
        except Exception as e:
            logger.error("User update failed", user_id=user_id, error=str(e))
            return None
    
    async def change_password(self, user_id: str, new_password: str) -> bool:
        """修改用户密码"""
        try:
            password_hash = self._hash_password(new_password)
            
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        password_hash=password_hash,
                        updated_at=datetime.utcnow()
                    )
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    
                    # 清除缓存
                    self._invalidate_user_cache(user_id)
                    
                    logger.info("Password changed successfully", user_id=user_id)
                    
                    # 记录审计日志
                    await self._log_auth_event(user_id, "password_changed", True)
                    
                    return True
                    
                return False
                
        except Exception as e:
            logger.error("Password change failed", user_id=user_id, error=str(e))
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    delete(UserModel).where(UserModel.id == user_id)
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    
                    # 清除缓存
                    self._invalidate_user_cache(user_id)
                    
                    logger.info("User deleted successfully", user_id=user_id)
                    
                    # 记录审计日志
                    await self._log_auth_event(user_id, "user_deleted", True)
                    
                    # 更新指标
                    self.metrics["total_users"] -= 1
                    
                    return True
                    
                return False
                
        except Exception as e:
            logger.error("User deletion failed", user_id=user_id, error=str(e))
            return False
    
    # ========================================================================
    # 安全管理方法
    # ========================================================================
    
    async def _handle_failed_login(self, user: Dict[str, Any]):
        """处理登录失败"""
        try:
            user_id = user["id"]
            failed_attempts = user["failed_login_attempts"] + 1
            
            # 检查是否需要锁定账户
            locked_until = None
            if failed_attempts >= self.max_failed_attempts:
                locked_until = datetime.utcnow() + self.lockout_duration
                logger.warning("User account locked due to failed attempts", 
                             user_id=user_id, attempts=failed_attempts)
            
            async with self.db_manager.get_session() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        failed_login_attempts=failed_attempts,
                        locked_until=locked_until,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            # 清除缓存
            self._invalidate_user_cache(user_id)
            
            # 更新指标
            self.metrics["failed_attempts_today"] += 1
            if locked_until:
                self.metrics["locked_users"] += 1
            
        except Exception as e:
            logger.error("Handle failed login error", error=str(e))
    
    async def _reset_failed_attempts(self, user_id: str):
        """重置失败尝试计数"""
        try:
            async with self.db_manager.get_session() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        failed_login_attempts=0,
                        locked_until=None,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            # 清除缓存
            self._invalidate_user_cache(user_id)
            
        except Exception as e:
            logger.error("Reset failed attempts error", error=str(e))
    
    async def _update_last_login(self, user_id: str):
        """更新最后登录时间"""
        try:
            async with self.db_manager.get_session() as session:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(
                        last_login=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            # 清除缓存
            self._invalidate_user_cache(user_id)
            
        except Exception as e:
            logger.error("Update last login error", error=str(e))
    
    async def update_last_login(self, user_id: str):
        """公共方法：更新最后登录时间"""
        await self._update_last_login(user_id)
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _invalidate_user_cache(self, user_id: str):
        """清除用户缓存"""
        keys_to_remove = []
        for key in self._user_cache:
            if key.startswith(f"user_id:{user_id}") or key.endswith(f":{user_id}"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._user_cache[key]
    
    async def _create_default_admin(self):
        """创建默认管理员用户"""
        try:
            # 检查是否已存在admin用户
            admin_user = await self.get_user_by_username("admin")
            if admin_user:
                return
            
            # 创建默认管理员
            admin_data = {
                "username": "admin",
                "email": "admin@reusable-iam.local",
                "password": "admin123",  # 生产环境应该修改
                "first_name": "System",
                "last_name": "Administrator",
                "display_name": "System Administrator",
                "roles": ["admin", "user"],
                "primary_role": "admin",
                "is_active": True,
                "email_verified": True
            }
            
            user_id = await self.create_user(admin_data)
            if user_id:
                logger.warning("Default admin user created - please change password in production!")
            else:
                logger.error("Failed to create default admin user")
                
        except Exception as e:
            logger.error("Create default admin failed", error=str(e))
    
    async def _log_auth_event(self, user_id: Optional[str], event_type: str, 
                            success: bool, metadata: Optional[Dict[str, Any]] = None):
        """记录认证事件"""
        try:
            async with self.db_manager.get_session() as session:
                event = AuditLogModel(
                    id=secrets.token_urlsafe(16),
                    user_id=user_id,
                    event_type=event_type,
                    success=success,
                    metadata=metadata or {},
                    created_at=datetime.utcnow()
                )
                
                session.add(event)
                await session.commit()
                
        except Exception as e:
            logger.error("Log auth event failed", error=str(e))
    
    async def _update_metrics(self):
        """更新服务指标"""
        try:
            async with self.db_manager.get_session() as session:
                # 总用户数
                result = await session.execute(
                    select(func.count(UserModel.id))
                )
                self.metrics["total_users"] = result.scalar() or 0
                
                # 活跃用户数
                result = await session.execute(
                    select(func.count(UserModel.id))
                    .where(UserModel.is_active == True)
                )
                self.metrics["active_users"] = result.scalar() or 0
                
                # 锁定用户数
                result = await session.execute(
                    select(func.count(UserModel.id))
                    .where(UserModel.locked_until > datetime.utcnow())
                )
                self.metrics["locked_users"] = result.scalar() or 0
                
        except Exception as e:
            logger.error("Update metrics failed", error=str(e))
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取服务指标"""
        await self._update_metrics()
        return self.metrics.copy()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单查询测试数据库连接
            async with self.db_manager.get_session() as session:
                await session.execute(select(1))
                return True
        except Exception:
            return False