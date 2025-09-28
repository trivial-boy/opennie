# 记账App API文档

## 基础信息

- **Base URL**: `http://192.168.0.173:8000/api/v1` (开发环境)
- **认证方式**: Bearer Token (JWT)
- **Content-Type**: `application/json`
- **时区**: UTC

## 环境配置

### 服务器配置
- **开发环境**: 配置文件位于 `backend/.env.development`
- **服务器地址**: 由 `SERVER_HOST` 和 `SERVER_PORT` 环境变量控制
- **当前配置**: `SERVER_HOST=0.0.0.0`, `SERVER_PORT=8000`
- **局域网访问**: 服务器绑定到 `0.0.0.0`，支持局域网内其他设备访问

### 邮件验证配置
- **功能开关**: `EMAIL_VERIFICATION_ENABLED` (当前为 `false`)
- **当前状态**: 邮件验证功能已禁用，用户注册后可直接登录
- **Token过期时间**: `ACCESS_TOKEN_EXPIRE_MINUTES=30` (30分钟)

### 启动服务
```bash
cd backend
python run.py
```

### 测试API
```bash
# 运行认证测试
cd backend
python -m pytest tests/test_auth.py -v
```

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据不合法",
    "details": [
      {
        "field": "email",
        "reason": "邮箱格式不正确"
      }
    ]
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### 分页响应
```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| SUCCESS | 200 | 成功 |
| VALIDATION_ERROR | 400 | 输入验证错误 |
| UNAUTHORIZED | 401 | 未授权 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| EMAIL_NOT_VERIFIED | 422 | 邮箱未验证 |
| VERIFICATION_CODE_EXPIRED | 422 | 验证码已过期 |
| VERIFICATION_CODE_INVALID | 422 | 验证码无效 |
| EMAIL_ALREADY_EXISTS | 409 | 邮箱已存在 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 1. 用户认证 (Auth)

### 1.1 用户注册
```http
POST /auth/register
```

**请求体:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "email_verified": false,
    "avatar_url": null,
    "created_at": "2024-01-01T00:00:00.000Z"
  },
  "message": "注册成功，验证邮件已发送到您的邮箱，请查收并验证邮箱后登录",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

> **注意**: 如果邮件验证功能被禁用(`EMAIL_VERIFICATION_ENABLED=false`)，用户注册后可直接登录，`email_verified`字段将为`true`。
```

### 1.2 发送邮箱验证码
```http
POST /auth/send-verification-email
```

**请求体:**
```json
{
  "email": "john@example.com"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "message": "验证邮件已发送",
    "email": "john@example.com",
    "expires_in": 1800
  },
  "message": "操作成功",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### 1.3 验证邮箱
```http
POST /auth/verify-email
```

**请求体 (通过验证码):**
```json
{
  "email": "john@example.com",
  "verification_code": "123456"
}
```

**或者 (通过令牌):**
```json
{
  "verification_token": "verification_token_from_email"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "message": "邮箱验证成功",
    "email": "john@example.com"
  },
  "message": "操作成功",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### 1.4 用户登录
```http
POST /auth/login
```

**请求体:**
```json
{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "username": "john_doe",
      "email": "john@example.com",
      "email_verified": true,
      "avatar_url": null,
      "created_at": "2024-01-01T00:00:00.000Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 1800
  },
  "message": "操作成功",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

> **注意**: 
> - `expires_in` 值由配置文件中的 `ACCESS_TOKEN_EXPIRE_MINUTES` 决定(默认30分钟=1800秒)
> - 如果邮件验证功能启用但用户邮箱未验证，将返回422错误
```

**错误响应 (邮箱未验证):**
```json
{
  "detail": "邮箱未验证，请先验证邮箱后登录"
}
```

### 1.5 刷新Token
```http
POST /auth/refresh
```

**请求头:**
```
Authorization: Bearer <refresh_token>
```

**响应:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 1800
  },
  "message": "操作成功",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### 1.6 用户登出
```http
POST /auth/logout
```

**请求头:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "success": true,
  "data": {
    "message": "登出成功"
  },
  "message": "操作成功",
  "code": 200,
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

---

## 待实现的功能

以下功能在API设计中规划但尚未实现：

### 获取当前用户信息
```http
GET /auth/me
```

### 忘记密码
```http
POST /auth/forgot-password
```

### 重置密码
```http
POST /auth/reset-password
```

---

## 2. 账本管理 (Accounts)

> **⚠️ 重要提示**: 以下所有账本管理、账单管理、资产管理、分类管理、预算管理和报表统计功能仅为API设计文档，**尚未实现**。
> 
> **当前已实现的功能仅包括**:
> - ✅ 用户注册 (`POST /auth/register`)
> - ✅ 用户登录 (`POST /auth/login`) 
> - ✅ 邮箱验证 (`POST /auth/send-verification-email`, `POST /auth/verify-email`)
> - ✅ 刷新令牌 (`POST /auth/refresh`)
> - ✅ 用户登出 (`POST /auth/logout`)
>
> **开发进度**: 目前项目处于基础认证系统开发完成阶段，其他业务功能模块待后续开发。

## 2. 账本管理 (Accounts) ✅

### 2.1 获取账本列表
```http
GET /accounts?page=1&size=20
```

**响应:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "个人账本",
        "description": "我的个人财务记录",
        "currency": "CNY",
        "is_shared": false,
        "members": [],
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 1,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

### 2.2 创建账本
```http
POST /accounts
```

**请求体:**
```json
{
  "name": "家庭账本",
  "description": "家庭共同财务管理",
  "currency": "CNY",
  "is_shared": true,
  "members": ["uuid1", "uuid2"]
}
```

### 2.3 获取账本详情
```http
GET /accounts/{account_id}
```

### 2.4 更新账本
```http
PUT /accounts/{account_id}
```

### 2.5 删除账本
```http
DELETE /accounts/{account_id}
```

### 2.6 获取账本汇总
```http
GET /accounts/{account_id}/summary?start_date=2024-01-01&end_date=2024-01-31
```

**响应:**
```json
{
  "success": true,
  "data": {
    "total_income": 10000.00,
    "total_expense": 6000.00,
    "net_amount": 4000.00,
    "transaction_count": 25,
    "period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    }
  }
}
```

---

## 3. 账单管理 (Bills)

### 3.1 获取账单列表
```http
GET /bills?account_id=uuid&page=1&size=20&start_date=2024-01-01&end_date=2024-01-31&type=expense&category_id=uuid
```

**查询参数:**
- `account_id`: 账本ID (可选)
- `type`: 类型 (income/expense/transfer)
- `category_id`: 分类ID
- `start_date`: 开始日期
- `end_date`: 结束日期
- `page`: 页码
- `size`: 每页数量

**响应:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "account_id": "uuid",
        "asset_id": "uuid",
        "category_id": "uuid",
        "amount": 100.00,
        "currency": "CNY",
        "type": "expense",
        "description": "午餐",
        "date": "2024-01-01",
        "created_at": "2024-01-01T12:00:00Z",
        "account": {
          "id": "uuid",
          "name": "个人账本"
        },
        "asset": {
          "id": "uuid",
          "name": "招商银行卡",
          "type": "bank_account"
        },
        "category": {
          "id": "uuid",
          "name": "餐饮",
          "icon": "🍽️",
          "color": "#FF6B6B"
        }
      }
    ],
    "pagination": {...}
  }
}
```

### 3.2 创建账单
```http
POST /bills
```

**请求体:**
```json
{
  "account_id": "uuid",
  "asset_id": "uuid",
  "category_id": "uuid",
  "amount": 100.00,
  "currency": "CNY",
  "type": "expense",
  "description": "午餐",
  "date": "2024-01-01"
}
```

### 3.3 获取账单详情
```http
GET /bills/{bill_id}
```

### 3.4 更新账单
```http
PUT /bills/{bill_id}
```

### 3.5 删除账单
```http
DELETE /bills/{bill_id}
```

### 3.6 按天聚合账单
```http
GET /bills/daily-summary?account_id=uuid&start_date=2024-01-01&end_date=2024-01-31
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-01",
      "total_income": 0.00,
      "total_expense": 300.00,
      "net_amount": -300.00,
      "transaction_count": 3,
      "bills": [
        {
          "id": "uuid",
          "amount": 100.00,
          "type": "expense",
          "description": "午餐",
          "category": {
            "name": "餐饮",
            "icon": "🍽️"
          }
        }
      ]
    }
  ]
}
```

### 3.7 批量导入账单
```http
POST /bills/batch-import
```

**请求体 (multipart/form-data):**
```
file: CSV文件
account_id: uuid
```

**CSV格式示例:**
```csv
date,amount,type,description,category_name,asset_name
2024-01-01,100.00,expense,午餐,餐饮,招商银行卡
2024-01-01,50.00,expense,地铁,交通,现金
```

---

## 4. 资产管理 (Assets)

### 4.1 获取资产列表
```http
GET /assets?type=bank_account&include_in_total=true
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "招商银行卡",
      "type": "bank_account",
      "balance": 15000.00,
      "currency": "CNY",
      "include_in_total": true,
      "notes": "主要储蓄账户",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 4.2 创建资产
```http
POST /assets
```

**请求体:**
```json
{
  "name": "支付宝余额",
  "type": "cash",
  "balance": 500.00,
  "currency": "CNY",
  "include_in_total": true,
  "notes": "日常小额支付"
}
```

### 4.3 获取资产详情
```http
GET /assets/{asset_id}
```

### 4.4 更新资产
```http
PUT /assets/{asset_id}
```

### 4.5 删除资产
```http
DELETE /assets/{asset_id}
```

### 4.6 获取资产总览
```http
GET /assets/overview
```

**响应:**
```json
{
  "success": true,
  "data": {
    "total_assets": 50000.00,
    "positive_assets": 52000.00,
    "liabilities": 2000.00,
    "net_worth": 50000.00,
    "asset_count": 8,
    "liability_ratio": 0.04,
    "asset_breakdown": [
      {
        "type": "bank_account",
        "count": 3,
        "total_balance": 30000.00,
        "percentage": 0.6
      },
      {
        "type": "investment",
        "count": 2,
        "total_balance": 15000.00,
        "percentage": 0.3
      }
    ]
  }
}
```

### 4.7 获取资产趋势
```http
GET /assets/trends?period=6months&asset_id=uuid
```

**响应:**
```json
{
  "success": true,
  "data": {
    "period": "6months",
    "data_points": [
      {
        "date": "2024-01-01",
        "total_assets": 45000.00,
        "net_worth": 43000.00
      },
      {
        "date": "2024-02-01",
        "total_assets": 47000.00,
        "net_worth": 45000.00
      }
    ],
    "growth": {
      "amount": 5000.00,
      "percentage": 0.11
    }
  }
}
```

---

## 5. 分类管理 (Categories)

### 5.1 获取分类列表
```http
GET /categories?type=expense&parent_id=uuid
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "餐饮",
      "type": "expense",
      "icon": "🍽️",
      "color": "#FF6B6B",
      "parent_id": null,
      "children": [
        {
          "id": "uuid",
          "name": "早餐",
          "icon": "🌅",
          "color": "#FF6B6B"
        }
      ],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 5.2 创建分类
```http
POST /categories
```

**请求体:**
```json
{
  "name": "健身",
  "type": "expense",
  "icon": "💪",
  "color": "#4ECDC4",
  "parent_id": null
}
```

### 5.3 更新分类
```http
PUT /categories/{category_id}
```

### 5.4 删除分类
```http
DELETE /categories/{category_id}
```

---

## 6. 预算管理 (Budgets)

### 6.1 获取预算列表
```http
GET /budgets?account_id=uuid&period_type=monthly&year=2024
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "account_id": "uuid",
      "name": "2024年1月预算",
      "total_amount": 5000.00,
      "period_type": "monthly",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "categories": [
        {
          "category_id": "uuid",
          "category_name": "餐饮",
          "allocated_amount": 1000.00,
          "spent_amount": 800.00,
          "remaining_amount": 200.00,
          "usage_percentage": 0.8
        }
      ],
      "total_spent": 3200.00,
      "remaining_amount": 1800.00,
      "usage_percentage": 0.64,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 6.2 创建预算
```http
POST /budgets
```

**请求体:**
```json
{
  "account_id": "uuid",
  "name": "2024年2月预算",
  "total_amount": 5500.00,
  "period_type": "monthly",
  "start_date": "2024-02-01",
  "end_date": "2024-02-29",
  "categories": [
    {
      "category_id": "uuid",
      "allocated_amount": 1200.00
    },
    {
      "category_id": "uuid",
      "allocated_amount": 800.00
    }
  ]
}
```

### 6.3 获取预算详情
```http
GET /budgets/{budget_id}
```

### 6.4 更新预算
```http
PUT /budgets/{budget_id}
```

### 6.5 删除预算
```http
DELETE /budgets/{budget_id}
```

### 6.6 获取预算执行进度
```http
GET /budgets/{budget_id}/progress
```

**响应:**
```json
{
  "success": true,
  "data": {
    "budget": {
      "id": "uuid",
      "name": "2024年1月预算",
      "total_amount": 5000.00,
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "progress": {
      "total_spent": 3200.00,
      "remaining_amount": 1800.00,
      "usage_percentage": 0.64,
      "days_elapsed": 15,
      "days_remaining": 16,
      "daily_average_spent": 213.33,
      "projected_total": 4960.00,
      "is_on_track": true
    },
    "categories": [
      {
        "category_id": "uuid",
        "category_name": "餐饮",
        "allocated_amount": 1000.00,
        "spent_amount": 800.00,
        "remaining_amount": 200.00,
        "usage_percentage": 0.8,
        "status": "warning",
        "daily_average": 53.33
      }
    ],
    "alerts": [
      {
        "type": "category_overspend",
        "category_name": "娱乐",
        "message": "娱乐分类已超出预算20%"
      }
    ]
  }
}
```

---

## 7. 报表统计 (Reports)

### 7.1 收支汇总
```http
GET /reports/summary?account_id=uuid&start_date=2024-01-01&end_date=2024-01-31&group_by=month
```

**响应:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "group_by": "month"
    },
    "summary": {
      "total_income": 15000.00,
      "total_expense": 8000.00,
      "net_amount": 7000.00,
      "transaction_count": 45
    },
    "groups": [
      {
        "period": "2024-01",
        "total_income": 15000.00,
        "total_expense": 8000.00,
        "net_amount": 7000.00,
        "transaction_count": 45
      }
    ]
  }
}
```

### 7.2 趋势分析
```http
GET /reports/trends?account_id=uuid&period=6months&metric=expense&group_by=month
```

**响应:**
```json
{
  "success": true,
  "data": {
    "metric": "expense",
    "period": "6months",
    "group_by": "month",
    "data_points": [
      {
        "period": "2023-08",
        "value": 6500.00,
        "change": 0.0,
        "change_percentage": 0.0
      },
      {
        "period": "2023-09",
        "value": 7200.00,
        "change": 700.00,
        "change_percentage": 0.108
      }
    ],
    "statistics": {
      "average": 7100.00,
      "min": 6500.00,
      "max": 8200.00,
      "total_change": 1700.00,
      "total_change_percentage": 0.262
    }
  }
}
```

### 7.3 分类统计
```http
GET /reports/categories?account_id=uuid&start_date=2024-01-01&end_date=2024-01-31&type=expense
```

**响应:**
```json
{
  "success": true,
  "data": {
    "type": "expense",
    "total_amount": 8000.00,
    "categories": [
      {
        "category_id": "uuid",
        "category_name": "餐饮",
        "category_icon": "🍽️",
        "category_color": "#FF6B6B",
        "amount": 2400.00,
        "percentage": 0.3,
        "transaction_count": 24,
        "average_amount": 100.00,
        "trend": {
          "previous_period_amount": 2200.00,
          "change": 200.00,
          "change_percentage": 0.091
        }
      }
    ],
    "top_categories": [
      {
        "rank": 1,
        "category_name": "餐饮",
        "amount": 2400.00,
        "percentage": 0.3
      }
    ]
  }
}
```

### 7.4 对比分析
```http
GET /reports/comparison?account_id=uuid&period1_start=2024-01-01&period1_end=2024-01-31&period2_start=2023-01-01&period2_end=2023-01-31
```

**响应:**
```json
{
  "success": true,
  "data": {
    "period1": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "total_income": 15000.00,
      "total_expense": 8000.00,
      "net_amount": 7000.00
    },
    "period2": {
      "start_date": "2023-01-01",
      "end_date": "2023-01-31",
      "total_income": 12000.00,
      "total_expense": 7500.00,
      "net_amount": 4500.00
    },
    "comparison": {
      "income_change": 3000.00,
      "income_change_percentage": 0.25,
      "expense_change": 500.00,
      "expense_change_percentage": 0.067,
      "net_change": 2500.00,
      "net_change_percentage": 0.556
    },
    "category_comparison": [
      {
        "category_name": "餐饮",
        "period1_amount": 2400.00,
        "period2_amount": 2000.00,
        "change": 400.00,
        "change_percentage": 0.2
      }
    ]
  }
}
```

---

## 8. 债务管理 (Debts)

### 8.1 获取债务列表
```http
GET /debts?type=borrow_in&is_settled=false
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "type": "borrow_in",
      "counterpart": "张三",
      "amount": 5000.00,
      "currency": "CNY",
      "description": "创业资金借款",
      "due_date": "2024-06-01",
      "is_settled": false,
      "days_until_due": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 8.2 创建债务记录
```http
POST /debts
```

**请求体:**
```json
{
  "type": "lend_out",
  "counterpart": "李四",
  "amount": 2000.00,
  "currency": "CNY",
  "description": "朋友急用",
  "due_date": "2024-03-01"
}
```

### 8.3 更新债务记录
```http
PUT /debts/{debt_id}
```

### 8.4 结清债务
```http
POST /debts/{debt_id}/settle
```

### 8.5 删除债务记录
```http
DELETE /debts/{debt_id}
```

---

## 9. 周期账单 (Recurring Bills)

### 9.1 获取周期账单列表
```http
GET /recurring-bills?is_active=true&frequency=monthly
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Netflix订阅",
      "amount": 68.00,
      "currency": "CNY",
      "asset_id": "uuid",
      "category_id": "uuid",
      "frequency": "monthly",
      "next_due_date": "2024-02-01",
      "end_date": null,
      "is_active": true,
      "description": "视频流媒体服务",
      "asset": {
        "name": "信用卡"
      },
      "category": {
        "name": "娱乐",
        "icon": "🎬"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 9.2 创建周期账单
```http
POST /recurring-bills
```

**请求体:**
```json
{
  "name": "手机话费",
  "amount": 89.00,
  "currency": "CNY",
  "asset_id": "uuid",
  "category_id": "uuid",
  "frequency": "monthly",
  "next_due_date": "2024-02-05",
  "end_date": null,
  "description": "中国移动月租费"
}
```

### 9.3 更新周期账单
```http
PUT /recurring-bills/{recurring_bill_id}
```

### 9.4 执行周期账单
```http
POST /recurring-bills/{recurring_bill_id}/execute
```

**请求体:**
```json
{
  "execution_date": "2024-02-01",
  "amount": 68.00,
  "description": "Netflix订阅 - 2024年2月"
}
```

### 9.5 暂停/恢复周期账单
```http
POST /recurring-bills/{recurring_bill_id}/toggle
```

### 9.6 删除周期账单
```http
DELETE /recurring-bills/{recurring_bill_id}
```

---

## 10. AI对话 (AI)

### 10.1 发送AI对话
```http
POST /ai/chat
```

**请求体:**
```json
{
  "message": "本周我花了多少钱在餐饮上？",
  "session_id": "uuid",
  "account_id": "uuid"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "response": "根据您的账单记录，本周(1月22日-1月28日)您在餐饮分类上总共花费了420元，包括15笔交易。",
    "sql_query": "SELECT SUM(amount) FROM bills WHERE user_id = ? AND category_id IN (SELECT id FROM categories WHERE name = '餐饮') AND date BETWEEN '2024-01-22' AND '2024-01-28'",
    "query_result": {
      "total_amount": 420.00,
      "transaction_count": 15,
      "details": [
        {
          "date": "2024-01-22",
          "amount": 65.00,
          "description": "午餐"
        }
      ]
    },
    "suggestions": [
      "查看餐饮分类的历史趋势",
      "与上月同期对比",
      "查看最大单笔餐饮支出"
    ]
  }
}
```

### 10.2 获取AI建议
```http
GET /ai/suggestions?account_id=uuid&type=budget
```

**响应:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "type": "budget_alert",
        "title": "餐饮预算即将超支",
        "description": "您本月的餐饮支出已达到预算的85%，建议控制后续支出",
        "priority": "medium",
        "action": "调整预算或减少支出"
      },
      {
        "type": "saving_opportunity",
        "title": "投资建议",
        "description": "您的现金资产较多，可以考虑进行一些低风险投资",
        "priority": "low",
        "action": "查看投资选项"
      }
    ]
  }
}
```

### 10.3 获取对话历史
```http
GET /ai/conversations?session_id=uuid&page=1&size=20
```

---

## 11. 文件上传 (Uploads)

### 11.1 上传图片
```http
POST /uploads/image
```

**请求体 (multipart/form-data):**
```
file: 图片文件
purpose: bill_receipt | avatar | other
```

**响应:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "file_name": "receipt_20240101.jpg",
    "file_path": "https://cdn.example.com/uploads/images/uuid.jpg",
    "file_size": 1024000,
    "mime_type": "image/jpeg",
    "recognition_result": {
      "amount": 125.50,
      "merchant": "星巴克",
      "date": "2024-01-01",
      "items": [
        {
          "name": "美式咖啡",
          "price": 35.00
        },
        {
          "name": "三明治",
          "price": 90.50
        }
      ]
    }
  }
}
```

### 11.2 上传语音
```http
POST /uploads/voice
```

**请求体 (multipart/form-data):**
```
file: 音频文件
format: wav | mp3 | m4a
```

**响应:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "file_path": "https://cdn.example.com/uploads/voice/uuid.wav",
    "transcription": "今天午餐花了八十五块钱在湘菜馆",
    "recognition_result": {
      "amount": 85.00,
      "description": "午餐",
      "suggested_category": "餐饮",
      "confidence": 0.92
    }
  }
}
```

### 11.3 上传CSV文件
```http
POST /uploads/csv
```

**请求体 (multipart/form-data):**
```
file: CSV文件
source: alipay | wechat | bank | other
account_id: uuid
```

**响应:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "file_name": "alipay_bills_202401.csv",
    "preview": [
      {
        "date": "2024-01-01",
        "amount": 100.00,
        "description": "午餐",
        "merchant": "麦当劳",
        "mapped_category": "餐饮"
      }
    ],
    "total_records": 156,
    "import_status": "pending",
    "mapping_suggestions": {
      "amount_column": "金额",
      "date_column": "交易时间",
      "description_column": "商品说明"
    }
  }
}
```

### 11.4 确认CSV导入
```http
POST /uploads/{upload_id}/import
```

**请求体:**
```json
{
  "column_mapping": {
    "date": "交易时间",
    "amount": "金额",
    "description": "商品说明",
    "merchant": "交易对方"
  },
  "category_mapping": {
    "餐饮": "uuid",
    "交通": "uuid"
  },
  "skip_duplicates": true
}
```

---

## 12. 通知和提醒 (Notifications)

### 12.1 获取通知列表
```http
GET /notifications?is_read=false&type=budget_alert
```

### 12.2 标记通知为已读
```http
PUT /notifications/{notification_id}/read
```

### 12.3 获取通知设置
```http
GET /notifications/settings
```

### 12.4 更新通知设置
```http
PUT /notifications/settings
```

---

## 13. 系统配置 (System)

### 13.1 获取汇率信息
```http
GET /system/exchange-rates?from=USD&to=CNY
```

### 13.2 获取系统配置
```http
GET /system/config
```

**响应:**
```json
{
  "success": true,
  "data": {
    "supported_currencies": ["CNY", "USD", "EUR", "JPY", "GBP"],
    "default_currency": "CNY",
    "file_upload_limits": {
      "max_size": 10485760,
      "allowed_types": ["jpg", "png", "pdf", "csv"]
    },
    "features": {
      "ai_chat": true,
      "voice_recognition": true,
      "image_recognition": true
    }
  }
}
```

---

## 认证和权限

### JWT Token格式
```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "iat": 1704067200,
  "exp": 1704070800,
  "type": "access"
}
```

### 权限级别
- **owner**: 账本创建者，拥有全部权限
- **admin**: 管理员，可管理账本和成员
- **member**: 普通成员，可查看和记账
- **viewer**: 只读权限

### 请求头示例
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
Accept: application/json
X-Request-ID: uuid (可选，用于请求追踪)
```

---

## 限流和配额

- **认证接口**: 10次/分钟
- **文件上传**: 20次/小时
- **AI对话**: 100次/天
- **一般API**: 1000次/小时

## WebSocket接口

### 连接地址
```
wss://api.billapp.com/ws?token=jwt_token
```

### 实时事件
```json
{
  "type": "bill_created",
  "data": {
    "account_id": "uuid",
    "bill": {...}
  }
}

{
  "type": "budget_alert",
  "data": {
    "budget_id": "uuid",
    "message": "预算即将超支"
  }
}
```
