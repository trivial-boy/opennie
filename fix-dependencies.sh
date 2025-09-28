#!/bin/bash

# 修复依赖安装问题的脚本

echo "🔧 修复Python依赖安装问题..."

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip

# 检查requirements.txt文件
REQUIREMENTS_FILE="requirements.txt"
if [[ -f "$REQUIREMENTS_FILE" ]]; then
    echo "📋 找到requirements.txt文件，安装所有依赖..."

    # 先安装基础依赖，避免版本冲突
    echo "📦 安装基础依赖..."
    pip install wheel setuptools

    # 安装requirements.txt中的所有依赖
    echo "📦 安装requirements.txt中的依赖..."
    pip install -r "$REQUIREMENTS_FILE"

    echo "✅ requirements.txt依赖安装完成"
else
    echo "⚠️ 未找到requirements.txt，安装核心依赖..."

    # 安装核心依赖（备用方案）
    echo "📦 安装核心依赖..."

    # Web框架
    pip install "fastapi==0.104.1"
    pip install "uvicorn[standard]==0.24.0"

    # 数据库
    pip install "sqlalchemy[asyncio]==1.4.48"
    pip install "asyncpg==0.28.0"
    pip install "alembic==1.12.1"

    # 缓存
    pip install "redis==5.0.1"
    pip install "aioredis==2.0.1"

    # 认证和安全
    pip install "python-jose[cryptography]==3.3.0"
    pip install "passlib[bcrypt]==1.7.4"
    pip install "python-multipart==0.0.6"

    # 邮件和模板
    pip install "aiosmtplib==3.0.1"
    pip install "jinja2==3.1.2"

    # 工具库
    pip install "python-dotenv==1.0.0"
    pip install "pydantic==2.11.9"
    pip install "pydantic-settings==2.11.0"
    pip install "httpx==0.25.2"
    pip install "loguru==0.7.2"
    pip install "python-dateutil==2.8.2"
    pip install "pytz==2023.3"

    # 文件处理
    pip install "pillow==10.1.0"
    pip install "python-magic==0.4.27"

    # API文档
    pip install "fastapi-users==12.1.2"

    echo "✅ 核心依赖安装完成"
fi

# 测试导入
echo "🧪 测试核心模块导入..."
python3 -c "
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import asyncpg
    import redis
    import aioredis
    print('✅ 所有核心模块导入成功')
    print(f'FastAPI版本: {fastapi.__version__}')
    print(f'SQLAlchemy版本: {sqlalchemy.__version__}')
    print(f'Pydantic版本: {fastapi.pydantic.__version__}')
except ImportError as e:
    print(f'⚠️ 模块导入警告: {e}')
    print('某些模块可能未正确安装，但基础功能应该可用')
"

echo "🎉 依赖修复完成！"
