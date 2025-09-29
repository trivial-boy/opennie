#!/bin/bash

# 容器启动脚本 - 安装依赖并启动应用

set -e

echo "🚀 启动记账App容器..."

# 配置pip3国内镜像源
echo "🔧 配置pip3国内镜像源..."
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip3 config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装Python依赖
echo "📦 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    echo "使用 requirements.txt 安装依赖..."
    pip3 install --no-cache-dir -r requirements.txt
else
    echo "❌ 未找到 requirements.txt 文件"
    exit 1
fi

# 检查关键依赖是否安装成功
echo "🔍 检查关键依赖..."
python3 -c "import fastapi; print('✅ FastAPI 安装成功')" || exit 1
python3 -c "import sqlalchemy; print('✅ SQLAlchemy 安装成功')" || exit 1
python3 -c "import redis; print('✅ Redis 安装成功')" || exit 1

# 等待数据库和Redis服务启动
echo "⏳ 等待数据库和Redis服务启动..."
sleep 10

# 启动应用
echo "🎯 启动记账App应用..."
exec python3 run.py
