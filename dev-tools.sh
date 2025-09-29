#!/bin/bash

# 开发者工具脚本 - 提供常用的开发操作

set -e

# 显示帮助信息
show_help() {
    echo "🛠️ 记账App开发者工具"
    echo ""
    echo "使用方法: ./dev-tools.sh [选项]"
    echo ""
    echo "可用选项:"
    echo "  restart      快速重启app容器"
    echo "  redeploy     拉取代码并重新部署"
    echo "  logs         查看app实时日志"
    echo "  status       查看服务状态"
    echo "  shell        进入app容器shell"
    echo "  clean        清理Docker资源"
    echo "  health       检查应用健康状态"
    echo "  help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./dev-tools.sh restart    # 快速重启"
    echo "  ./dev-tools.sh logs       # 查看日志"
    echo "  ./dev-tools.sh redeploy   # 代码同步重部署"
    echo ""
}

# 快速重启
restart_app() {
    echo "🔄 快速重启app..."
    ./restart-app.sh
}

# 代码同步重部署
redeploy_app() {
    echo "🔄 代码同步重部署..."
    ./redeploy.sh
}

# 查看日志
show_logs() {
    echo "📋 显示app实时日志（按Ctrl+C退出）..."
    docker-compose logs -f app
}

# 查看状态
show_status() {
    echo "📊 服务状态:"
    docker-compose ps

    echo ""
    echo "🐳 Docker资源使用:"
    docker stats --no-stream

    echo ""
    echo "💾 磁盘使用:"
    docker system df
}

# 进入容器shell
enter_shell() {
    echo "🐚 进入app容器shell..."
    if docker-compose ps app | grep -q "Up"; then
        docker-compose exec app bash
    else
        echo "❌ app容器未运行，请先启动服务"
        exit 1
    fi
}

# 清理Docker资源
clean_docker() {
    echo "🧹 清理Docker资源..."
    read -p "是否清理未使用的Docker资源? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "清理中..."
        docker system prune -f
        docker volume prune -f
        echo "✅ 清理完成"
    else
        echo "已取消清理"
    fi
}

# 健康检查
health_check() {
    echo "🏥 检查应用健康状态..."

    # 检查容器状态
    if docker-compose ps app | grep -q "Up"; then
        echo "✅ App容器运行中"

        # 检查健康端点
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ 应用健康检查通过"
            echo "🌐 访问地址:"
            echo "  - 本地: http://localhost:8000"
            echo "  - 内网: http://172.16.2.50:8000"
            echo "  - API文档: http://172.16.2.50:8000/docs"
        else
            echo "❌ 应用健康检查失败"
            echo "💡 建议查看日志: ./dev-tools.sh logs"
        fi
    else
        echo "❌ App容器未运行"
        echo "💡 建议启动服务: ./deploy.sh 或 ./restart-app.sh"
    fi

    # 检查数据库和Redis
    echo ""
    echo "🔍 检查依赖服务:"
    if docker-compose ps mysql | grep -q "Up"; then
        echo "✅ MySQL运行中"
    else
        echo "❌ MySQL未运行"
    fi

    if docker-compose ps redis | grep -q "Up"; then
        echo "✅ Redis运行中"
    else
        echo "❌ Redis未运行"
    fi
}

# 主逻辑
case "${1:-help}" in
    restart)
        restart_app
        ;;
    redeploy)
        redeploy_app
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    shell)
        enter_shell
        ;;
    clean)
        clean_docker
        ;;
    health)
        health_check
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知选项: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
