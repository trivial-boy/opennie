#!/bin/bash

# 记账App Docker部署脚本

set -e

echo "🚀 开始部署记账App..."

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p docker/mysql docker/redis uploads logs

# 检查Docker和Docker Compose是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装Docker Compose"
    exit 1
fi

# 停止现有容器（如果存在）
echo "🛑 停止现有容器..."
docker-compose down

# 清理悬空镜像（可选）
echo "🧹 清理悬空镜像..."
docker image prune -f

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 检查应用健康状态
echo "🏥 检查应用健康状态..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 应用启动成功！"
        break
    else
        echo "⏳ 等待应用启动... ($i/10)"
        sleep 5
    fi

    if [ $i -eq 10 ]; then
        echo "❌ 应用启动失败，请检查日志"
        docker-compose logs app
        exit 1
    fi
done

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 服务信息:"
echo "  - 应用地址: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - MySQL: localhost:3306"
echo "  - Redis: localhost:6379"
echo ""
echo "📝 默认账号信息:"
echo "  - MySQL用户: user"
echo "  - MySQL密码: opennie@123"
echo "  - Redis密码: opennie@123"
echo ""
echo "🔧 常用命令:"
echo "  - 查看日志: docker-compose logs -f [服务名]"
echo "  - 停止服务: docker-compose down"
echo "  - 重启服务: docker-compose restart [服务名]"
echo "  - 进入容器: docker-compose exec [服务名] bash"
echo ""
