-- MySQL初始化脚本 - 记账App数据库

-- 设置字符集和时区
SET NAMES utf8mb4;
SET time_zone = '+08:00';

-- 使用数据库
USE accounting_db;

-- 创建数据库表（基于现有的PostgreSQL schema转换为MySQL）

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 账本表
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    currency VARCHAR(3) DEFAULT 'CNY',
    is_shared BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_accounts_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 资产表
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'CNY',
    include_in_total BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_assets_user_id (user_id),
    INDEX idx_assets_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 分类表
CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    icon VARCHAR(10),
    color VARCHAR(7),
    parent_id VARCHAR(36),
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_categories_user_id (user_id),
    INDEX idx_categories_type (type),
    INDEX idx_categories_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 账单表
CREATE TABLE IF NOT EXISTS bills (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    asset_id VARCHAR(36),
    category_id VARCHAR(36),
    to_account_id VARCHAR(36),
    to_asset_id VARCHAR(36),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    type VARCHAR(20) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_bills_user_id (user_id),
    INDEX idx_bills_account_id (account_id),
    INDEX idx_bills_date (date),
    INDEX idx_bills_type (type),
    INDEX idx_bills_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 预算表
CREATE TABLE IF NOT EXISTS budgets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_budgets_user_id (user_id),
    INDEX idx_budgets_account_id (account_id),
    INDEX idx_budgets_period (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 预算分类表
CREATE TABLE IF NOT EXISTS budget_categories (
    id VARCHAR(36) PRIMARY KEY,
    budget_id VARCHAR(36) NOT NULL,
    category_id VARCHAR(36) NOT NULL,
    allocated_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_budget_categories_budget_id (budget_id),
    INDEX idx_budget_categories_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 债务表
CREATE TABLE IF NOT EXISTS debts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    type VARCHAR(20) NOT NULL,
    counterparty VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    description TEXT,
    due_date DATE,
    is_settled BOOLEAN DEFAULT FALSE,
    settled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_debts_user_id (user_id),
    INDEX idx_debts_type (type),
    INDEX idx_debts_due_date (due_date),
    INDEX idx_debts_is_settled (is_settled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 周期账单表
CREATE TABLE IF NOT EXISTS recurring_bills (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    account_id VARCHAR(36) NOT NULL,
    asset_id VARCHAR(36),
    category_id VARCHAR(36),
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    type VARCHAR(20) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    next_execution_date DATE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_recurring_bills_user_id (user_id),
    INDEX idx_recurring_bills_account_id (account_id),
    INDEX idx_recurring_bills_next_execution (next_execution_date),
    INDEX idx_recurring_bills_frequency (frequency),
    INDEX idx_recurring_bills_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建系统默认分类
INSERT IGNORE INTO categories (id, user_id, name, type, icon, color, is_system) VALUES
('sys_income_salary', NULL, '工资', 'income', '💰', '#28a745', TRUE),
('sys_income_bonus', NULL, '奖金', 'income', '🎁', '#28a745', TRUE),
('sys_income_investment', NULL, '投资收益', 'income', '📈', '#28a745', TRUE),
('sys_expense_food', NULL, '餐饮', 'expense', '🍽️', '#dc3545', TRUE),
('sys_expense_transport', NULL, '交通', 'expense', '🚗', '#dc3545', TRUE),
('sys_expense_shopping', NULL, '购物', 'expense', '🛍️', '#dc3545', TRUE),
('sys_expense_entertainment', NULL, '娱乐', 'expense', '🎮', '#dc3545', TRUE),
('sys_expense_utilities', NULL, '水电费', 'expense', '💡', '#dc3545', TRUE),
('sys_expense_rent', NULL, '房租', 'expense', '🏠', '#dc3545', TRUE),
('sys_transfer', NULL, '转账', 'transfer', '🔄', '#6c757d', TRUE);

-- 输出初始化完成信息
SELECT 'MySQL数据库初始化完成' as status;
