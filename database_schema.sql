-- 记账App数据库建表语句 (PostgreSQL)
-- 创建数据库
-- CREATE DATABASE bill_app WITH ENCODING 'UTF8' LC_COLLATE = 'C' LC_CTYPE = 'C' TEMPLATE template0;

-- 如果需要重置数据库，请先运行 reset_database.sql 脚本

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建UUID v7生成函数
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS UUID
AS $$
DECLARE
    unix_ts_ms BIGINT;
    uuid_bytes BYTEA;
BEGIN
    -- 获取当前时间戳(毫秒)
    unix_ts_ms := FLOOR(EXTRACT(EPOCH FROM clock_timestamp()) * 1000);

    -- 构造UUID v7
    -- 前48位：时间戳(毫秒)
    -- 12位：版本号(7) + 随机数
    -- 2位：变体位 + 62位随机数
    uuid_bytes :=
        SUBSTRING(INT8SEND(unix_ts_ms), 3, 6) ||  -- 48位时间戳
        SUBSTRING(uuid_send(gen_random_uuid()), 7, 2) ||  -- 12位随机数，设置版本号
        SUBSTRING(uuid_send(gen_random_uuid()), 9, 8);    -- 64位随机数，设置变体位

    -- 设置版本号为7 (第13个半字节)
    uuid_bytes := SET_BYTE(uuid_bytes, 6, (GET_BYTE(uuid_bytes, 6) & 15) | 112);

    -- 设置变体位为10 (第17个bit)
    uuid_bytes := SET_BYTE(uuid_bytes, 8, (GET_BYTE(uuid_bytes, 8) & 63) | 128);

    RETURN ENCODE(uuid_bytes, 'hex')::UUID;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- 创建枚举类型
CREATE TYPE asset_type_enum AS ENUM ('bank_account', 'credit_card', 'cash', 'investment', 'property', 'other');
CREATE TYPE transaction_type_enum AS ENUM ('income', 'expense', 'transfer');
CREATE TYPE period_type_enum AS ENUM ('weekly', 'monthly', 'quarterly', 'yearly');
CREATE TYPE frequency_enum AS ENUM ('daily', 'weekly', 'monthly', 'yearly');
CREATE TYPE debt_type_enum AS ENUM ('borrow_in', 'lend_out');
CREATE TYPE file_type_enum AS ENUM ('image', 'voice', 'csv', 'other');

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- 添加注释
COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.id IS '用户唯一标识';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.password_hash IS '密码哈希';
COMMENT ON COLUMN users.email_verified IS '邮箱是否已验证';
COMMENT ON COLUMN users.email_verified_at IS '邮箱验证时间';
COMMENT ON COLUMN users.avatar_url IS '头像URL';

-- 账本表
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    currency VARCHAR(3) DEFAULT 'CNY',
    is_shared BOOLEAN DEFAULT FALSE,
    members JSONB DEFAULT '[]', -- 多人协作成员ID列表
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_created_at ON accounts(created_at);
CREATE INDEX idx_accounts_members ON accounts USING GIN(members);

-- 添加注释
COMMENT ON TABLE accounts IS '账本表';
COMMENT ON COLUMN accounts.members IS '多人协作成员ID列表(JSON格式)';

-- 资产表
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    type asset_type_enum NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'CNY',
    include_in_total BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_assets_user_id ON assets(user_id);
CREATE INDEX idx_assets_type ON assets(type);
CREATE INDEX idx_assets_include_in_total ON assets(include_in_total);

-- 添加注释
COMMENT ON TABLE assets IS '资产表';
COMMENT ON COLUMN assets.include_in_total IS '是否计入总资产';

-- 分类表
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    name VARCHAR(50) NOT NULL,
    type transaction_type_enum NOT NULL,
    icon VARCHAR(50),
    color VARCHAR(7), -- 颜色代码，如#FF5733
    parent_id UUID, -- 父分类ID，支持子分类
    is_system BOOLEAN DEFAULT FALSE, -- 是否为系统默认分类
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_categories_type ON categories(type);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_is_system ON categories(is_system);

-- 添加注释
COMMENT ON TABLE categories IS '分类表';
COMMENT ON COLUMN categories.parent_id IS '父分类ID，支持子分类';
COMMENT ON COLUMN categories.color IS '颜色代码，如#FF5733';
COMMENT ON COLUMN categories.is_system IS '是否为系统默认分类';

-- 账单表
CREATE TABLE bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    account_id UUID NOT NULL,
    asset_id UUID NOT NULL,
    category_id UUID NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    type transaction_type_enum NOT NULL,
    description VARCHAR(255),
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_bills_user_id ON bills(user_id);
CREATE INDEX idx_bills_account_id ON bills(account_id);
CREATE INDEX idx_bills_asset_id ON bills(asset_id);
CREATE INDEX idx_bills_category_id ON bills(category_id);
CREATE INDEX idx_bills_date ON bills(date);
CREATE INDEX idx_bills_type ON bills(type);
CREATE INDEX idx_bills_created_at ON bills(created_at);
CREATE INDEX idx_bills_user_date ON bills(user_id, date);
CREATE INDEX idx_bills_amount ON bills(amount);

-- 添加注释
COMMENT ON TABLE bills IS '账单表';

-- 预算表
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    account_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    period_type period_type_enum NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_budgets_user_id ON budgets(user_id);
CREATE INDEX idx_budgets_account_id ON budgets(account_id);
CREATE INDEX idx_budgets_period ON budgets(start_date, end_date);
CREATE INDEX idx_budgets_period_type ON budgets(period_type);

-- 添加注释
COMMENT ON TABLE budgets IS '预算表';

-- 预算分类明细表
CREATE TABLE budget_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    budget_id UUID NOT NULL,
    category_id UUID NOT NULL,
    allocated_amount DECIMAL(15,2) NOT NULL,
    spent_amount DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(budget_id, category_id)
);

-- 创建索引
CREATE INDEX idx_budget_categories_budget_id ON budget_categories(budget_id);
CREATE INDEX idx_budget_categories_category_id ON budget_categories(category_id);

-- 添加注释
COMMENT ON TABLE budget_categories IS '预算分类明细表';

-- 周期账单表（订阅、分期）
CREATE TABLE recurring_bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    template_bill_id UUID NOT NULL, -- 模板账单ID
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    asset_id UUID NOT NULL,
    category_id UUID NOT NULL,
    frequency frequency_enum NOT NULL,
    next_due_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_recurring_bills_user_id ON recurring_bills(user_id);
CREATE INDEX idx_recurring_bills_asset_id ON recurring_bills(asset_id);
CREATE INDEX idx_recurring_bills_category_id ON recurring_bills(category_id);
CREATE INDEX idx_recurring_bills_next_due_date ON recurring_bills(next_due_date);
CREATE INDEX idx_recurring_bills_is_active ON recurring_bills(is_active);
CREATE INDEX idx_recurring_bills_frequency ON recurring_bills(frequency);

-- 添加注释
COMMENT ON TABLE recurring_bills IS '周期账单表';
COMMENT ON COLUMN recurring_bills.template_bill_id IS '模板账单ID';

-- 债务表
CREATE TABLE debts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    type debt_type_enum NOT NULL,
    counterpart VARCHAR(100) NOT NULL, -- 对方姓名或机构
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    description VARCHAR(255),
    due_date DATE,
    is_settled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_debts_user_id ON debts(user_id);
CREATE INDEX idx_debts_type ON debts(type);
CREATE INDEX idx_debts_is_settled ON debts(is_settled);
CREATE INDEX idx_debts_due_date ON debts(due_date);

-- 添加注释
COMMENT ON TABLE debts IS '债务表';
COMMENT ON COLUMN debts.type IS 'borrow_in:借入, lend_out:借出';
COMMENT ON COLUMN debts.counterpart IS '对方姓名或机构';

-- 文件上传记录表
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type file_type_enum NOT NULL,
    file_size INTEGER NOT NULL, -- 文件大小(字节)
    mime_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_file_type ON uploads(file_type);
CREATE INDEX idx_uploads_created_at ON uploads(created_at);

-- 添加注释
COMMENT ON TABLE uploads IS '文件上传记录表';
COMMENT ON COLUMN uploads.file_size IS '文件大小(字节)';

-- AI对话记录表
CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL, -- 会话ID
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    sql_query TEXT, -- 生成的SQL查询语句
    query_result JSONB, -- SQL查询结果
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_ai_conversations_user_id ON ai_conversations(user_id);
CREATE INDEX idx_ai_conversations_session_id ON ai_conversations(session_id);
CREATE INDEX idx_ai_conversations_created_at ON ai_conversations(created_at);
CREATE INDEX idx_ai_conversations_query_result ON ai_conversations USING GIN(query_result);

-- 添加注释
COMMENT ON TABLE ai_conversations IS 'AI对话记录表';
COMMENT ON COLUMN ai_conversations.session_id IS '会话ID';
COMMENT ON COLUMN ai_conversations.sql_query IS '生成的SQL查询语句';
COMMENT ON COLUMN ai_conversations.query_result IS 'SQL查询结果';

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    device_info VARCHAR(255),
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- 添加注释
COMMENT ON TABLE user_sessions IS '用户会话表';

-- 系统配置表
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_system_configs_key ON system_configs(config_key);

-- 添加注释
COMMENT ON TABLE system_configs IS '系统配置表';

-- 邮箱验证表
CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL,
    email VARCHAR(100) NOT NULL,
    verification_code VARCHAR(6) NOT NULL,
    verification_token VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL DEFAULT 'registration', -- 'registration', 'password_reset'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX idx_email_verifications_email ON email_verifications(email);
CREATE INDEX idx_email_verifications_token ON email_verifications(verification_token);
CREATE INDEX idx_email_verifications_code ON email_verifications(verification_code);
CREATE INDEX idx_email_verifications_expires_at ON email_verifications(expires_at);

-- 添加注释
COMMENT ON TABLE email_verifications IS '邮箱验证表';
COMMENT ON COLUMN email_verifications.verification_code IS '6位数字验证码';
COMMENT ON COLUMN email_verifications.verification_token IS '验证令牌(用于URL验证)';
COMMENT ON COLUMN email_verifications.type IS '验证类型: registration(注册), password_reset(密码重置)';
COMMENT ON COLUMN email_verifications.expires_at IS '验证码过期时间';
COMMENT ON COLUMN email_verifications.used_at IS '使用时间';
COMMENT ON COLUMN email_verifications.is_used IS '是否已使用';

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要自动更新updated_at字段的表创建触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budget_categories_updated_at BEFORE UPDATE ON budget_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recurring_bills_updated_at BEFORE UPDATE ON recurring_bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_debts_updated_at BEFORE UPDATE ON debts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configs_updated_at BEFORE UPDATE ON system_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认系统配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('default_currency', 'CNY', '默认货币'),
('exchange_rate_api_key', '', '汇率API密钥'),
('file_upload_max_size', '10485760', '文件上传最大大小(10MB)'),
('ai_service_endpoint', '', 'AI服务接口地址'),
('session_expire_hours', '168', '会话过期时间(小时)');

-- 创建默认系统分类模板（不绑定用户，供新用户注册时复制）
-- 支出分类模板
INSERT INTO categories (id, user_id, name, type, icon, color, is_system) VALUES
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '餐饮', 'expense', '🍽️', '#FF6B6B', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '交通', 'expense', '🚗', '#4ECDC4', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '购物', 'expense', '🛍️', '#45B7D1', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '娱乐', 'expense', '🎬', '#96CEB4', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '医疗', 'expense', '🏥', '#FFEAA7', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '教育', 'expense', '📚', '#DDA0DD', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '住房', 'expense', '🏠', '#98D8C8', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '其他', 'expense', '📦', '#A8A8A8', true);

-- 收入分类模板
INSERT INTO categories (id, user_id, name, type, icon, color, is_system) VALUES
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '工资', 'income', '💼', '#00D4AA', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '奖金', 'income', '🎁', '#FF9F43', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '投资收益', 'income', '📈', '#5F27CD', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '兼职', 'income', '💻', '#00D2D3', true),
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '其他收入', 'income', '💰', '#FFC312', true);

-- 转账分类模板
INSERT INTO categories (id, user_id, name, type, icon, color, is_system) VALUES
(uuid_generate_v7(), '00000000-0000-0000-0000-000000000000'::uuid, '账户转账', 'transfer', '↔️', '#747D8C', true);

-- 创建常用查询视图
-- 账单汇总视图
CREATE VIEW bill_summary AS
SELECT
    user_id,
    account_id,
    DATE_TRUNC('month', date) as month,
    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
    SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) as net_amount
FROM bills
GROUP BY user_id, account_id, DATE_TRUNC('month', date);

-- 资产总览视图
CREATE VIEW asset_overview AS
SELECT
    user_id,
    SUM(CASE WHEN include_in_total THEN balance ELSE 0 END) as total_assets,
    SUM(CASE WHEN balance >= 0 THEN balance ELSE 0 END) as positive_assets,
    SUM(CASE WHEN balance < 0 THEN ABS(balance) ELSE 0 END) as liabilities,
    COUNT(*) as asset_count
FROM assets
GROUP BY user_id;

-- 添加全文搜索索引
CREATE INDEX idx_bills_description_search ON bills USING gin(to_tsvector('simple', description));
CREATE INDEX idx_categories_name_search ON categories USING gin(to_tsvector('simple', name));
