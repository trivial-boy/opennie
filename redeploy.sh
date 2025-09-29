#!/bin/bash

# 代码同步并重新部署App服务脚本

set -e

echo "🔄 代码同步并重新部署记账App..."

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    echo "当前目录：$(pwd)"
    exit 1
fi

# 检查是否为Git仓库
if [ ! -d ".git" ]; then
    echo "❌ 错误：当前目录不是Git仓库"
    exit 1
fi

# 检查Docker和Docker Compose是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker服务未运行，请先启动Docker"
    exit 1
fi

# 显示当前Git状态
echo "📋 当前Git状态:"
git status --porcelain

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "⚠️ 检测到未提交的更改"
    read -p "是否先提交当前更改? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 提交当前更改..."
        git add .
        read -p "请输入提交信息: " commit_message
        git commit -m "$commit_message"
        echo "✅ 代码已提交"
    fi
fi

# 拉取最新代码
echo ""
echo "📥 拉取最新代码..."
git fetch origin

# 检查是否有远程更新
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ 代码已是最新版本"
else
    echo "🔄 发现远程更新，正在拉取..."
    git pull origin main
    echo "✅ 代码更新完成"
fi

# 显示最新提交信息
echo ""
echo "📋 最新提交信息:"
git log --oneline -3

# 停止app容器
echo ""
echo "🛑 停止app容器..."
docker-compose stop app

# 重新构建app容器（使用最新代码）
echo "🔨 重新构建app容器（使用最新代码）..."
docker-compose build --no-cache app

# 启动app容器
echo "🚀 启动app容器..."
docker-compose up -d app

# 等待服务启动
echo "⏳ 等待app服务启动（正在安装依赖）..."
sleep 30

# 检查容器状态
echo "🔍 检查容器状态..."
if docker-compose ps app | grep -q "Up"; then
    echo "✅ App容器启动成功！"

    # 显示容器日志（最后20行）
    echo ""
    echo "📋 容器启动日志（最后20行）:"
    docker-compose logs --tail=20 app

    # 显示服务信息
    echo ""
    echo "📋 服务信息:"
    echo "  - 本地访问: http://localhost:8000"
    echo "  - 内网访问: http://172.16.2.50:8000"
    echo "  - API文档: http://172.16.2.50:8000/docs"

    # 检查应用健康状态
    echo ""
    echo "🏥 检查应用健康状态..."
    for i in {1..10}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ 应用健康检查通过！"
            break
        else
            echo "⏳ 等待应用就绪... ($i/10)"
            sleep 10
        fi

        if [ $i -eq 10 ]; then
            echo "⚠️ 应用可能需要更多时间启动，请手动检查日志"
            echo "查看日志命令: docker-compose logs -f app"
        fi
    done
else
    echo "❌ App容器启动失败，请检查日志"
    echo "查看日志命令: docker-compose logs app"
    exit 1
fi

echo ""
echo "🎉 代码同步并重新部署完成！"
echo ""
echo "💡 常用命令："
echo "  - 查看实时日志: docker-compose logs -f app"
echo "  - 快速重启: ./restart-app.sh"
echo "  - 代码同步重部署: ./redeploy.sh"
echo "  - 停止服务: docker-compose stop app"
echo ""
