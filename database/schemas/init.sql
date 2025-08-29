-- =============================================================================
-- 独立IAM认证授权服务数据库初始化脚本
-- =============================================================================

-- 创建数据库（如果不存在）
-- CREATE DATABASE iam_service OWNER postgres;
-- \c iam_service;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- 用户和认证相关表
-- =============================================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    display_name VARCHAR(255),
    password_hash TEXT NOT NULL,
    
    -- 角色和权限
    roles TEXT[] DEFAULT ARRAY['user'],
    primary_role VARCHAR(255) DEFAULT 'user',
    
    -- 账户状态
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    
    -- 安全跟踪
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_failed_attempt TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL,
    refresh_token VARCHAR(255),
    
    -- 会话信息
    ip_address INET,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    
    -- 过期时间
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    refresh_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    
    -- 权限范围
    scopes TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- 状态和过期
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 授权相关表
-- =============================================================================

-- 策略表
CREATE TABLE IF NOT EXISTS policies (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    policy_id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 策略内容
    effect VARCHAR(50) NOT NULL DEFAULT 'deny', -- permit, deny, not_applicable, indeterminate
    conditions JSONB NOT NULL DEFAULT '{}',
    target JSONB DEFAULT '{}',
    
    -- 优先级和状态
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 元数据
    obligations TEXT[] DEFAULT ARRAY[]::TEXT[],
    advice TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- 审计信息
    created_by VARCHAR(255),
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(policy_id, version)
);

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- 角色层级
    parent_roles TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- 权限
    permissions JSONB DEFAULT '[]',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_system_role BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) UNIQUE NOT NULL,
    resource VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 权限条件
    conditions JSONB DEFAULT '{}',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(resource, action)
);

-- 角色权限映射表
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id VARCHAR(255) NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id VARCHAR(255) NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by VARCHAR(255),
    
    PRIMARY KEY (role_id, permission_id)
);

-- 用户角色映射表
CREATE TABLE IF NOT EXISTS user_roles (
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id VARCHAR(255) NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    PRIMARY KEY (user_id, role_id)
);

-- =============================================================================
-- 审计和日志表
-- =============================================================================

-- 认证事件日志
CREATE TABLE IF NOT EXISTS auth_events (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    
    -- 事件信息
    event_type VARCHAR(100) NOT NULL, -- login_success, login_failed, logout, token_refresh, etc.
    success BOOLEAN NOT NULL,
    
    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    
    -- 额外信息
    metadata JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 授权决策日志
CREATE TABLE IF NOT EXISTS authorization_decisions (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    decision_id VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::text,
    
    -- 请求信息
    user_id VARCHAR(255),
    resource_id VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    request_context JSONB DEFAULT '{}',
    
    -- 决策信息
    decision VARCHAR(50) NOT NULL, -- permit, deny, not_applicable, indeterminate
    policy_id VARCHAR(255),
    reason TEXT,
    attributes_used TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- 性能信息
    evaluation_time_ms NUMERIC(10,3) DEFAULT 0,
    cache_hit BOOLEAN DEFAULT FALSE,
    
    -- 额外信息
    obligations TEXT[] DEFAULT ARRAY[]::TEXT[],
    advice TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 系统审计日志
CREATE TABLE IF NOT EXISTS system_audit_log (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- 操作信息
    operation VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    
    -- 操作者信息
    performed_by VARCHAR(255),
    performed_by_type VARCHAR(50) DEFAULT 'user', -- user, system, api
    
    -- 变更信息
    old_values JSONB,
    new_values JSONB,
    changes JSONB DEFAULT '{}',
    
    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    
    -- 结果信息
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 配置和系统表
-- =============================================================================

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    
    -- 配置类型和分类
    config_type VARCHAR(100) DEFAULT 'application',
    category VARCHAR(100) DEFAULT 'general',
    
    -- 是否敏感（不在API中返回）
    is_sensitive BOOLEAN DEFAULT FALSE,
    
    -- 版本信息
    version INTEGER DEFAULT 1,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 服务健康检查表
CREATE TABLE IF NOT EXISTS service_health (
    service_name VARCHAR(255) PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    version VARCHAR(100),
    
    -- 健康检查信息
    last_check TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    check_interval_seconds INTEGER DEFAULT 30,
    
    -- 统计信息
    uptime_seconds BIGINT DEFAULT 0,
    total_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,
    
    -- 详细信息
    details JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 索引创建
-- =============================================================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_roles ON users USING GIN(roles);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 会话表索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- API密钥表索引
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- 策略表索引
CREATE INDEX IF NOT EXISTS idx_policies_policy_id ON policies(policy_id);
CREATE INDEX IF NOT EXISTS idx_policies_is_active ON policies(is_active);
CREATE INDEX IF NOT EXISTS idx_policies_priority ON policies(priority);
CREATE INDEX IF NOT EXISTS idx_policies_effect ON policies(effect);
CREATE INDEX IF NOT EXISTS idx_policies_conditions ON policies USING GIN(conditions);

-- 角色和权限索引
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_is_active ON roles(is_active);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON permissions(resource, action);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);

-- 审计日志索引
CREATE INDEX IF NOT EXISTS idx_auth_events_user_id ON auth_events(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_events_event_type ON auth_events(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_events_created_at ON auth_events(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_events_success ON auth_events(success);

CREATE INDEX IF NOT EXISTS idx_authorization_decisions_user_id ON authorization_decisions(user_id);
CREATE INDEX IF NOT EXISTS idx_authorization_decisions_resource_id ON authorization_decisions(resource_id);
CREATE INDEX IF NOT EXISTS idx_authorization_decisions_decision ON authorization_decisions(decision);
CREATE INDEX IF NOT EXISTS idx_authorization_decisions_created_at ON authorization_decisions(created_at);
CREATE INDEX IF NOT EXISTS idx_authorization_decisions_policy_id ON authorization_decisions(policy_id);

CREATE INDEX IF NOT EXISTS idx_system_audit_log_operation ON system_audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_system_audit_log_performed_by ON system_audit_log(performed_by);
CREATE INDEX IF NOT EXISTS idx_system_audit_log_created_at ON system_audit_log(created_at);

-- =============================================================================
-- 触发器和函数
-- =============================================================================

-- 更新updated_at字段的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间戳触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_service_health_updated_at BEFORE UPDATE ON service_health 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 视图创建
-- =============================================================================

-- 活跃用户视图
CREATE OR REPLACE VIEW active_users AS
SELECT 
    id, username, email, display_name, roles, primary_role,
    last_login, created_at
FROM users 
WHERE is_active = TRUE;

-- 用户权限视图
CREATE OR REPLACE VIEW user_permissions AS
SELECT DISTINCT
    u.id as user_id,
    u.username,
    p.resource,
    p.action,
    p.name as permission_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.is_active = TRUE
  AND p.is_active = TRUE;

-- 最近认证事件视图
CREATE OR REPLACE VIEW recent_auth_events AS
SELECT 
    id, user_id, event_type, success, ip_address, created_at
FROM auth_events 
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- 授权统计视图
CREATE OR REPLACE VIEW authorization_stats AS
SELECT 
    DATE(created_at) as date,
    decision,
    COUNT(*) as count,
    AVG(evaluation_time_ms) as avg_evaluation_time,
    COUNT(CASE WHEN cache_hit THEN 1 END) as cache_hits
FROM authorization_decisions 
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY DATE(created_at), decision
ORDER BY date DESC, decision;

-- =============================================================================
-- 注释
-- =============================================================================

-- 表注释
COMMENT ON TABLE users IS '用户账户表';
COMMENT ON TABLE user_sessions IS '用户会话表';
COMMENT ON TABLE api_keys IS 'API密钥表';
COMMENT ON TABLE policies IS '授权策略表';
COMMENT ON TABLE roles IS '角色表';
COMMENT ON TABLE permissions IS '权限表';
COMMENT ON TABLE auth_events IS '认证事件日志';
COMMENT ON TABLE authorization_decisions IS '授权决策日志';
COMMENT ON TABLE system_audit_log IS '系统审计日志';

-- 列注释示例
COMMENT ON COLUMN users.roles IS '用户角色数组';
COMMENT ON COLUMN users.failed_login_attempts IS '失败登录尝试次数';
COMMENT ON COLUMN users.locked_until IS '账户锁定截止时间';
COMMENT ON COLUMN policies.effect IS '策略效果: permit, deny, not_applicable, indeterminate';
COMMENT ON COLUMN authorization_decisions.cache_hit IS '是否命中缓存';

-- =============================================================================
-- 数据库初始化完成
-- =============================================================================