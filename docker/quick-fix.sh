#!/bin/bash

# Docker镜像访问问题快速修复脚本

set -e

echo "🚑 Docker镜像访问权限问题快速修复..."

# 问题诊断
echo "🔍 诊断当前问题..."
echo "问题：阿里云镜像仓库访问权限受限"
echo "错误：pull access denied, repository does not exist or may require authorization"

# 解决方案1：切换到中科大镜像源
echo ""
echo "🛠️ 解决方案1：切换到中科大镜像源（推荐）"
echo "sed -i 's/registry.cn-hangzhou.aliyuncs.com/docker.mirrors.ustc.edu.cn/g' Dockerfile"
echo "sed -i 's/registry.cn-hangzhou.aliyuncs.com/docker.mirrors.ustc.edu.cn/g' docker-compose.yml"

read -p "是否执行方案1? (Y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$|^$ ]]; then
    echo "执行中..."
    cd /Users/yizhou/Desktop/vibecoding
    sed -i '' 's/registry.cn-hangzhou.aliyuncs.com/docker.mirrors.ustc.edu.cn/g' Dockerfile 2>/dev/null || true
    sed -i '' 's/registry.cn-hangzhou.aliyuncs.com/docker.mirrors.ustc.edu.cn/g' docker-compose.yml 2>/dev/null || true
    sed -i '' 's/registry.cn-hangzhou.aliyuncs.com/docker.mirrors.ustc.edu.cn/g' Dockerfile.alternative 2>/dev/null || true
    echo "✅ 已切换到中科大镜像源"

    echo ""
    echo "🚀 现在可以重新构建："
    echo "   docker-compose up --build"
    exit 0
fi

# 解决方案2：使用官方镜像
echo ""
echo "🛠️ 解决方案2：直接使用Docker官方镜像（较慢但稳定）"
read -p "是否使用官方镜像? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "执行中..."
    cd /Users/yizhou/Desktop/vibecoding
    sed -i '' 's/ARG DOCKER_REGISTRY=.*/ARG DOCKER_REGISTRY=docker.io/g' Dockerfile
    sed -i '' 's/DOCKER_REGISTRY: .*/DOCKER_REGISTRY: docker.io/g' docker-compose.yml
    echo "✅ 已切换到Docker官方镜像"

    echo ""
    echo "🚀 现在可以重新构建："
    echo "   docker-compose up --build"
    exit 0
fi

# 解决方案3：测试可用镜像源
echo ""
echo "🛠️ 解决方案3：测试并选择最快的镜像源"
read -p "是否测试镜像源速度? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "开始测试镜像源速度..."
    ./docker/test-mirror-speed.sh
    exit 0
fi

echo ""
echo "💡 手动修复建议："
echo "1. 编辑 Dockerfile，修改第3行："
echo "   ARG DOCKER_REGISTRY=docker.mirrors.ustc.edu.cn"
echo ""
echo "2. 编辑 docker-compose.yml，修改第47行："
echo "   DOCKER_REGISTRY: docker.mirrors.ustc.edu.cn"
echo ""
echo "3. 重新构建："
echo "   docker-compose up --build"
echo ""
echo "🌐 当前使用："
echo "   - docker.io (Docker官方镜像，稳定可靠)"
echo ""
echo "📝 注意：现在使用官方镜像，虽然下载较慢但最稳定"
echo ""
