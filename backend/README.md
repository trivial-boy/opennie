# 记账App后端API

基于FastAPI的现代化记账应用后端服务。

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### 安装依赖

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

### 数据库初始化

```bash
# 确保PostgreSQL服务运行
# 创建数据库
createdb bill_app

# 运行数据库脚本
psql -d bill_app -f ../database_schema.sql
```

### 启动服务

```bash
# 开发模式启动
python run.py

# 或使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问服务

- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
backend/
├── app/
│   ├── api/                # API路由
│   │   └── v1/            # API v1版本
│   │       ├── auth.py    # 认证相关
│   │       ├── users.py   # 用户管理
│   │       ├── accounts.py # 账本管理
│   │       ├── bills.py   # 账单管理
│   │       ├── assets.py  # 资产管理
│   │       ├── categories.py # 分类管理
│   │       └── budgets.py # 预算管理
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   ├── redis.py       # Redis连接
│   │   └── security.py    # 安全工具
│   ├── models/            # 数据模型
│   ├── schemas/           # API模式
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── main.py           # 主应用
├── tests/                # 测试文件
├── scripts/              # 脚本文件
├── requirements.txt      # 依赖包
├── .env.example         # 环境变量模板
└── run.py               # 启动脚本
```

## 🔧 开发指南

### 代码规范

```bash
# 代码格式化
black app/

# 代码检查
flake8 app/

# 类型检查
mypy app/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app tests/
```

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 📋 API文档

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/verify-email` - 验证邮箱

### 账本管理
- `GET /api/v1/accounts` - 获取账本列表
- `POST /api/v1/accounts` - 创建账本
- `GET /api/v1/accounts/{id}` - 获取账本详情
- `PUT /api/v1/accounts/{id}` - 更新账本
- `DELETE /api/v1/accounts/{id}` - 删除账本

### 账单管理
- `GET /api/v1/bills` - 获取账单列表
- `POST /api/v1/bills` - 创建账单
- `GET /api/v1/bills/{id}` - 获取账单详情
- `PUT /api/v1/bills/{id}` - 更新账单
- `DELETE /api/v1/bills/{id}` - 删除账单

更多API详情请访问: http://localhost:8000/docs

## 🔒 安全特性

- JWT令牌认证
- 邮箱验证机制
- CORS跨域配置
- SQL注入防护
- 密码安全哈希

## 🚀 部署

### Docker部署

```bash
# 构建镜像
docker build -t bookkeeping-api .

# 运行容器
docker run -p 8000:8000 bookkeeping-api
```

### 生产环境

```bash
# 安装生产依赖
pip install gunicorn

# 启动生产服务器
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📞 技术支持

- 项目文档: [API文档](../API文档.md)
- 技术方案: [技术方案](../技术方案.md)
- 问题反馈: [GitHub Issues](https://github.com/trivial-boy/opennie/issues)

---

*由AI协助开发 - 让技术为生活服务* 🤖✨