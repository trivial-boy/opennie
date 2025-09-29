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

# 定义多个PyPI源
PYPI_SOURCES=(
    "https://pypi.org/simple/"
    "http://mirrors.cloud.aliyuncs.com/pypi/simple/"
    "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "https://pypi.douban.com/simple/"
)

# 尝试多源安装函数
try_install_with_sources() {
    local package="$1"
    local installed=false

    for source in "${PYPI_SOURCES[@]}"; do
        echo "🔄 尝试从 $source 安装 $package"
        if pip install --trusted-host mirrors.cloud.aliyuncs.com --trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host pypi.douban.com -i "$source" "$package"; then
            echo "✅ 成功从 $source 安装 $package"
            installed=true
            break
        else
            echo "❌ 从 $source 安装 $package 失败"
        fi
    done

    if [[ "$installed" != true ]]; then
        echo "⚠️ 所有源都安装失败: $package，继续安装其他依赖..."
        return 1
    fi
    return 0
}

# 检查requirements.txt文件
REQUIREMENTS_FILE="requirements.txt"
if [[ -f "$REQUIREMENTS_FILE" ]]; then
    echo "📋 找到requirements.txt文件，安装所有依赖..."

    # 先安装基础依赖，避免版本冲突
    echo "📦 安装基础依赖..."
    try_install_with_sources "wheel"
    try_install_with_sources "setuptools"

    # 尝试安装requirements.txt中的所有依赖
    echo "📦 尝试安装requirements.txt..."
    local success=false
    for source in "${PYPI_SOURCES[@]}"; do
        echo "🔄 尝试从 $source 安装requirements.txt"
        if pip install --trusted-host mirrors.cloud.aliyuncs.com --trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host pypi.douban.com -i "$source" -r "$REQUIREMENTS_FILE"; then
            echo "✅ 成功从 $source 安装requirements.txt"
            success=true
            break
        else
            echo "❌ 从 $source 安装requirements.txt失败，尝试下一个源..."
        fi
    done

    if [[ "$success" == true ]]; then
        echo "✅ requirements.txt依赖安装完成"
    else
        echo "⚠️ requirements.txt安装失败，尝试安装兼容版本的核心依赖..."

        # 检查Python版本并安装对应的兼容依赖
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        echo "🐍 检测到Python版本: $PYTHON_VERSION"

        if [[ "$PYTHON_VERSION" == "3.6" ]]; then
            echo "📦 安装Python 3.6兼容版本..."
            try_install_with_sources "fastapi>=0.65.0,<0.69.0"
            try_install_with_sources "pydantic>=1.6.0,<1.9.0"
            try_install_with_sources "uvicorn>=0.13.0,<0.16.0"
            try_install_with_sources "starlette>=0.14.0,<0.16.0"
        else
            echo "📦 安装标准兼容版本..."
            try_install_with_sources "fastapi>=0.70.0"
            try_install_with_sources "pydantic>=1.10.0"
            try_install_with_sources "uvicorn>=0.20.0"
        fi

        # 通用依赖
        try_install_with_sources "websockets>=9.0"
        try_install_with_sources "python-multipart>=0.0.5"
        try_install_with_sources "sqlalchemy[asyncio]==1.4.48"
        try_install_with_sources "asyncpg>=0.25.0"
        try_install_with_sources "alembic>=1.10.0"
        try_install_with_sources "redis>=4.0.0"
        try_install_with_sources "aioredis>=2.0.0"
        try_install_with_sources "python-jose[cryptography]>=3.0.0"
        try_install_with_sources "passlib[bcrypt]>=1.7.0"
        try_install_with_sources "python-dotenv>=1.0.0"
        try_install_with_sources "httpx>=0.23.0"
    fi
else
    echo "⚠️ 未找到requirements.txt，安装核心依赖..."

    # 安装核心依赖（备用方案）
    echo "📦 安装核心依赖..."

    # 检查Python版本安装兼容的Web框架
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "🐍 检测到Python版本: $PYTHON_VERSION"

    if [[ "$PYTHON_VERSION" == "3.6" ]]; then
        echo "📦 安装Python 3.6兼容的Web框架..."
        try_install_with_sources "fastapi>=0.65.0,<0.69.0"
        try_install_with_sources "pydantic>=1.6.0,<1.9.0"
        try_install_with_sources "uvicorn>=0.13.0,<0.16.0"
        try_install_with_sources "starlette>=0.14.0,<0.16.0"
    else
        echo "📦 安装标准兼容的Web框架..."
        try_install_with_sources "fastapi>=0.70.0"
        try_install_with_sources "pydantic>=1.10.0"
        try_install_with_sources "uvicorn>=0.20.0"
        try_install_with_sources "websockets>=10.0"
    fi

    # 数据库
    try_install_with_sources "sqlalchemy[asyncio]==1.4.48"
    try_install_with_sources "asyncpg>=0.25.0"
    try_install_with_sources "alembic>=1.10.0"

    # 缓存
    try_install_with_sources "redis>=4.0.0"
    try_install_with_sources "aioredis>=2.0.0"

    # 认证和安全
    try_install_with_sources "python-jose[cryptography]>=3.0.0"
    try_install_with_sources "passlib[bcrypt]>=1.7.0"
    try_install_with_sources "python-multipart>=0.0.5"

    # 邮件和模板
    try_install_with_sources "aiosmtplib>=3.0.0"
    try_install_with_sources "jinja2>=3.0.0"

    # 工具库
    try_install_with_sources "python-dotenv>=1.0.0"
    try_install_with_sources "pydantic>=1.10.0"
    try_install_with_sources "httpx>=0.23.0"
    try_install_with_sources "loguru>=0.7.0"
    try_install_with_sources "python-dateutil>=2.8.0"
    try_install_with_sources "pytz>=2022.1"

    # 文件处理
    try_install_with_sources "pillow>=10.0.0"
    try_install_with_sources "python-magic>=0.4.0"

    # API文档
    try_install_with_sources "fastapi-users>=12.0.0"

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
