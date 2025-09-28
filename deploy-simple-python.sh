#!/bin/bash

# 简单Python服务部署脚本
# 直接部署FastAPI应用，使用开发环境配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本信息
echo -e "${BLUE}🚀 记账App Python服务部署脚本${NC}"
echo -e "${YELLOW}📍 使用配置: .env.development${NC}"
echo "=" * 50

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo -e "${YELLOW}📁 项目目录: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}📁 后端目录: $BACKEND_DIR${NC}"

# 检查目录和文件
check_prerequisites() {
    echo -e "\n${YELLOW}🔍 检查前置条件...${NC}"

    if [[ ! -d "$BACKEND_DIR" ]]; then
        echo -e "${RED}❌ backend目录不存在: $BACKEND_DIR${NC}"
        exit 1
    fi

    if [[ ! -f "$BACKEND_DIR/.env.development" ]]; then
        echo -e "${RED}❌ 开发环境配置文件不存在: $BACKEND_DIR/.env.development${NC}"
        exit 1
    fi

    if [[ ! -f "$BACKEND_DIR/requirements.txt" ]]; then
        echo -e "${RED}❌ requirements.txt不存在${NC}"
        exit 1
    fi

    if [[ ! -f "$BACKEND_DIR/run.py" ]]; then
        echo -e "${RED}❌ run.py不存在${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ 前置条件检查通过${NC}"
}

# 检查Python环境
check_python() {
    echo -e "\n${YELLOW}🐍 检查Python环境...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ python3 未安装${NC}"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"

    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip3 未安装${NC}"
        exit 1
    fi

    PIP_VERSION=$(pip3 --version)
    echo -e "${GREEN}✅ pip版本: $PIP_VERSION${NC}"
}

# 安装依赖
install_dependencies() {
    echo -e "\n${YELLOW}📦 安装Python依赖...${NC}"

    cd "$BACKEND_DIR"

    # 检查是否有虚拟环境
    if [[ -d "venv" ]]; then
        echo -e "${YELLOW}🔄 激活现有虚拟环境...${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}🔄 创建虚拟环境...${NC}"
        python3 -m venv venv
        source venv/bin/activate
    fi

    echo -e "${YELLOW}🔄 安装依赖包...${NC}"
    bash ../fix-dependencies.sh
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 停止现有服务
stop_existing_service() {
    echo -e "\n${YELLOW}🛑 停止现有服务...${NC}"

    # 查找并停止Python服务进程
    if pgrep -f "run.py" > /dev/null; then
        echo -e "${YELLOW}🔄 发现运行中的服务，正在停止...${NC}"
        pkill -f "run.py" || true
        sleep 2
    fi

    # 释放8000端口
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo -e "${YELLOW}🔄 释放8000端口...${NC}"
        lsof -ti:8000 | xargs kill -9 || true
        sleep 1
    fi

    echo -e "${GREEN}✅ 现有服务已停止${NC}"
}

# 启动服务
start_service() {
    echo -e "\n${YELLOW}🚀 启动Python服务...${NC}"

    cd "$BACKEND_DIR"

    # 激活虚拟环境
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    fi

    # 显示配置信息
    echo -e "${BLUE}📋 服务配置信息:${NC}"
    echo -e "   配置文件: .env.development"
    echo -e "   服务地址: 0.0.0.0:8000"
    echo -e "   调试模式: 开启"
    echo -e "   日志级别: DEBUG"

    # 启动服务
    echo -e "\n${YELLOW}🔄 启动FastAPI服务...${NC}"
    python3 run.py &

    SERVICE_PID=$!
    echo -e "${GREEN}✅ 服务已启动 (PID: $SERVICE_PID)${NC}"

    # 等待服务启动
    echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
    sleep 5

    # 检查服务状态
    if kill -0 $SERVICE_PID 2>/dev/null; then
        echo -e "${GREEN}✅ 服务运行正常${NC}"

        # 测试健康检查
        echo -e "${YELLOW}🔍 测试服务连接...${NC}"
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ 健康检查通过${NC}"
        else
            echo -e "${YELLOW}⚠️ 健康检查失败，但服务可能正在启动中${NC}"
        fi

        return 0
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    echo -e "\n${BLUE}🎉 部署完成！${NC}"
    echo -e "${GREEN}=" * 50 "${NC}"
    echo -e "${GREEN}🌐 服务访问地址:${NC}"
    echo -e "   📍 API根地址: http://localhost:8000"
    echo -e "   📍 健康检查: http://localhost:8000/health"
    echo -e "   📍 API文档: http://localhost:8000/docs"
    echo -e "   📍 ReDoc文档: http://localhost:8000/redoc"

    echo -e "\n${GREEN}🛠️ 管理命令:${NC}"
    echo -e "   查看日志: tail -f $BACKEND_DIR/server.log"
    echo -e "   停止服务: pkill -f run.py"
    echo -e "   重启服务: $0"

    echo -e "\n${GREEN}📋 配置信息:${NC}"
    echo -e "   环境: 开发环境 (development)"
    echo -e "   配置文件: .env.development"
    echo -e "   调试模式: 开启"
    echo -e "   端口: 8000"

    echo -e "\n${YELLOW}💡 提示:${NC}"
    echo -e "   - 服务会自动重载代码变更"
    echo -e "   - 可以直接修改代码测试"
    echo -e "   - 使用Ctrl+C停止前台服务"
}

# 主函数
main() {
    echo -e "${BLUE}开始部署记账App Python服务...${NC}"

    # 执行部署步骤
    check_prerequisites
    check_python
    install_dependencies
    stop_existing_service

    if start_service; then
        show_service_info
        echo -e "\n${GREEN}🎉 部署成功！${NC}"

        # 保持脚本运行，显示日志
        echo -e "\n${YELLOW}📝 实时日志 (Ctrl+C 退出):${NC}"
        echo -e "${YELLOW}=" * 30 "${NC}"

        # 跟踪服务进程
        cd "$BACKEND_DIR"
        if [[ -d "venv" ]]; then
            source venv/bin/activate
        fi

        # 等待并显示日志
        sleep 2
        tail -f server.log 2>/dev/null || echo -e "${YELLOW}等待日志文件生成...${NC}"

    else
        echo -e "\n${RED}❌ 部署失败！${NC}"
        exit 1
    fi
}

# 捕获中断信号
trap 'echo -e "\n${YELLOW}🛑 收到中断信号，保持服务运行...${NC}"; exit 0' INT

# 运行主函数
main "$@"
