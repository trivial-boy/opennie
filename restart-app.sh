#!/bin/bash

# 快速重启App服务脚本

set -e

echo "🔄 快速重启记账App服务..."

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    echo "当前目录：$(pwd)"
    exit 1
fi

# 检查Docker和Docker Compose是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker服务未运行，请先启动Docker"
    exit 1
fi

# 停止app容器
echo "🛑 停止app容器..."
docker-compose stop app

# 重新构建app容器
echo "🔨 重新构建app容器..."
docker-compose build app

# 启动app容器
echo "🚀 启动app容器..."
docker-compose up -d app

# 等待服务启动
echo "⏳ 等待app服务启动..."
sleep 20

# 检查容器状态
echo "🔍 检查容器状态..."
if docker-compose ps app | grep -q "Up"; then
    echo "✅ App容器启动成功！"

    # 显示服务信息
    echo ""
    echo "📋 服务信息:"
    echo "  - 本地访问: http://localhost:8000"
    echo "  - 内网访问: http://172.16.2.50:8000"
    echo "  - API文档: http://172.16.2.50:8000/docs"

    # 检查应用健康状态
    echo ""
    echo "🏥 检查应用健康状态..."
    for i in {1..6}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ 应用健康检查通过！"
            break
        else
            echo "⏳ 等待应用就绪... ($i/6)"
            sleep 10
        fi

        if [ $i -eq 6 ]; then
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
echo "🎉 App服务重启完成！"
echo ""
echo "💡 常用命令："
echo "  - 查看日志: docker-compose logs -f app"
echo "  - 重启服务: ./restart-app.sh"
echo "  - 停止服务: docker-compose stop app"
echo ""
