#!/bin/bash

# 容器启动脚本 - 安装依赖并启动应用

set -e

echo "🚀 启动记账App容器..."
echo "当前目录: $(pwd)"
echo "Python版本: $(python3 --version)"
echo "pip版本: $(pip3 --version)"

# 配置pip3国内镜像源
echo "🔧 配置pip3国内镜像源..."
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip3 config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 检查requirements.txt文件
echo "📄 检查requirements.txt文件..."
if [ -f "requirements.txt" ]; then
    echo "✅ 找到 requirements.txt 文件"
    echo "文件内容预览:"
    head -10 requirements.txt
    echo "..."
    tail -5 requirements.txt
else
    echo "❌ 未找到 requirements.txt 文件"
    ls -la
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
echo "开始安装依赖，这可能需要几分钟..."
if pip3 install --no-cache-dir -r requirements.txt; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    echo "检查pip安装日志:"
    pip3 list
    exit 1
fi

# 检查关键依赖是否安装成功
echo "🔍 检查关键依赖..."
python3 -c "import fastapi; print('✅ FastAPI 安装成功')" || { echo "❌ FastAPI 安装失败"; exit 1; }
python3 -c "import sqlalchemy; print('✅ SQLAlchemy 安装成功')" || { echo "❌ SQLAlchemy 安装失败"; exit 1; }
python3 -c "import redis; print('✅ Redis 安装成功')" || { echo "❌ Redis 安装失败"; exit 1; }
python3 -c "import requests; print('✅ Requests 安装成功')" || { echo "❌ Requests 安装失败"; exit 1; }

# 等待数据库和Redis服务启动
echo "⏳ 等待数据库和Redis服务启动..."
sleep 10

# 检查run.py文件
echo "📄 检查run.py文件..."
if [ -f "run.py" ]; then
    echo "✅ 找到 run.py 文件"
else
    echo "❌ 未找到 run.py 文件"
    ls -la
    exit 1
fi

# 启动应用
echo "🎯 启动记账App应用..."
echo "执行命令: python3 run.py"
exec python3 run.py
