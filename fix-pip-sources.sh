#!/bin/bash

# 修复pip源问题的脚本

echo "🔧 诊断和修复pip源问题..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}📍 当前pip配置:${NC}"
pip config list || echo "无自定义配置"

echo -e "\n${YELLOW}🔍 测试不同pip源的连接性:${NC}"

# 测试不同的pip源
python3 -c "
import urllib.request
import sys

sources = [
    ('官方PyPI', 'https://pypi.org/simple/fastapi/'),
    ('阿里云镜像', 'http://mirrors.cloud.aliyuncs.com/pypi/simple/fastapi/'),
    ('清华镜像', 'https://pypi.tuna.tsinghua.edu.cn/simple/fastapi/'),
    ('中科大镜像', 'https://pypi.mirrors.ustc.edu.cn/simple/fastapi/'),
    ('华为云镜像', 'https://repo.huaweicloud.com/repository/pypi/simple/fastapi/')
]

working_sources = []

for name, url in sources:
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'pip/21.0')
        response = urllib.request.urlopen(req, timeout=5)
        print(f'✅ {name}: 可访问 (状态码: {response.status})')
        if 'fastapi' in response.read().decode().lower():
            working_sources.append((name, url.replace('/fastapi/', '')))
    except Exception as e:
        print(f'❌ {name}: 无法访问 ({type(e).__name__})')

print(f'\n📋 可用的pip源:')
for i, (name, base_url) in enumerate(working_sources, 1):
    print(f'{i}. {name}: {base_url}')
"

echo -e "\n${YELLOW}🛠️ 推荐的解决方案:${NC}"

# 创建一个智能的requirements安装脚本
cat > install-requirements-smart.sh << 'EOF'
#!/bin/bash

echo "🚀 智能安装Python依赖..."

# 可用的pip源列表（按优先级排序）
SOURCES=(
    "https://pypi.org/simple/"
    "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "https://pypi.mirrors.ustc.edu.cn/simple/"
    "https://repo.huaweicloud.com/repository/pypi/simple/"
    "http://mirrors.cloud.aliyuncs.com/pypi/simple/"
)

# 核心依赖列表（兼容版本）
CORE_PACKAGES=(
    "fastapi>=0.80.0,<0.90.0"
    "uvicorn[standard]>=0.20.0,<0.25.0"
    "sqlalchemy[asyncio]==1.4.48"
    "asyncpg>=0.25.0,<0.30.0"
    "alembic>=1.10.0,<1.15.0"
    "redis>=4.0.0,<6.0.0"
    "aioredis>=2.0.0,<3.0.0"
    "python-jose[cryptography]>=3.0.0,<4.0.0"
    "passlib[bcrypt]>=1.7.0,<2.0.0"
    "python-multipart>=0.0.5,<1.0.0"
    "aiosmtplib>=1.1.0,<4.0.0"
    "jinja2>=3.0.0,<4.0.0"
    "python-dotenv>=0.19.0,<2.0.0"
    "pydantic>=1.10.0,<2.0.0"
    "httpx>=0.23.0,<1.0.0"
    "python-dateutil>=2.8.0,<3.0.0"
    "pytz>=2022.1"
)

install_with_source() {
    local source=$1
    local package=$2
    echo "📦 尝试从 $source 安装 $package"

    if pip install --index-url "$source" --trusted-host "${source#*://}" "$package" --timeout 30; then
        return 0
    else
        return 1
    fi
}

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip

success_count=0
total_packages=${#CORE_PACKAGES[@]}

for package in "${CORE_PACKAGES[@]}"; do
    installed=false

    for source in "${SOURCES[@]}"; do
        if install_with_source "$source" "$package"; then
            echo "✅ $package 安装成功 (源: $source)"
            ((success_count++))
            installed=true
            break
        fi
    done

    if [ "$installed" = false ]; then
        echo "❌ $package 安装失败"
    fi
done

echo ""
echo "📊 安装结果: $success_count/$total_packages 成功"

if [ $success_count -eq $total_packages ]; then
    echo "🎉 所有依赖安装成功！"

    # 测试导入
    echo "🧪 测试核心模块..."
    python3 -c "
try:
    import fastapi, uvicorn, sqlalchemy, asyncpg, redis
    print('✅ 核心模块测试通过')
    print(f'FastAPI: {fastapi.__version__}')
    print(f'SQLAlchemy: {sqlalchemy.__version__}')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    "
else
    echo "⚠️ 部分依赖安装失败，请检查网络连接或尝试手动安装"
fi
EOF

chmod +x install-requirements-smart.sh

echo -e "${GREEN}✅ 创建了智能安装脚本: install-requirements-smart.sh${NC}"
echo -e "${YELLOW}💡 使用方法:${NC}"
echo -e "   cd backend && source venv/bin/activate && ../install-requirements-smart.sh"

echo -e "\n${YELLOW}🔧 问题分析:${NC}"
echo -e "1. 你的本地环境使用官方PyPI源 (https://pypi.org/simple/)"
echo -e "2. 服务器可能配置了阿里云镜像，但该镜像版本较旧"
echo -e "3. 建议在部署脚本中指定可用的pip源"

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Investigate pip source differences between local and server environments", "status": "completed", "activeForm": "Completed pip source investigation"}]
