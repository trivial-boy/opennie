#!/bin/bash

# 修复依赖安装问题的脚本

echo "🔧 修复Python依赖安装问题..."

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 升级pip3
echo "📦 升级pip3..."
pip3 install --upgrade pip3

# 安装核心依赖（使用兼容版本）
echo "📦 安装核心依赖..."

# Web框架
pip33 install "fastapi>=0.80.0,<0.90.0"
pip3 install "uvicorn[standard]>=0.20.0,<0.25.0"

# 数据库
pip3 install "sqlalchemy[asyncio]==1.4.48"
pip3 install "asyncpg>=0.25.0,<0.30.0"
pip3 install "alembic>=1.10.0,<1.15.0"

# 缓存
pip3 install "redis>=4.0.0,<6.0.0"
pip3 install "aioredis>=2.0.0,<3.0.0"

# 认证和安全
pip3 install "python-jose[cryptography]>=3.0.0,<4.0.0"
pip3 install "passlib[bcrypt]>=1.7.0,<2.0.0"
pip3 install "python-multipart>=0.0.5,<1.0.0"

# 邮件和模板
pip3 install "aiosmtplib>=1.1.0,<4.0.0"
pip3 install "jinja2>=3.0.0,<4.0.0"

# 工具库
pip3 install "python-dotenv>=0.19.0,<2.0.0"
pip3 install "pydantic>=1.10.0,<2.0.0"
pip3 install "httpx>=0.23.0,<1.0.0"
pip3 install "python-dateutil>=2.8.0,<3.0.0"
pip3 install "pytz>=2022.1"

echo "✅ 核心依赖安装完成"

# 测试导入
echo "🧪 测试核心模块导入..."
python3 -c "
import fastapi
import uvicorn
import sqlalchemy
import asyncpg
import redis
import aioredis
print('✅ 所有核心模块导入成功')
print(f'FastAPI版本: {fastapi.__version__}')
print(f'SQLAlchemy版本: {sqlalchemy.__version__}')
"

echo "🎉 依赖修复完成！"
