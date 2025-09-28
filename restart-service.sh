#!/bin/bash

# 快速重启记账App服务脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 重启记账App服务...${NC}"

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"

# 停止现有服务
echo -e "${YELLOW}🛑 停止现有服务...${NC}"
pkill -f "run.py" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# 启动服务
echo -e "${YELLOW}🚀 启动服务...${NC}"
cd "$BACKEND_DIR"

# 激活虚拟环境（如果存在）
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# 后台启动服务
nohup python3 run.py > server.log 2>&1 &
SERVICE_PID=$!

echo -e "${GREEN}✅ 服务已启动 (PID: $SERVICE_PID)${NC}"

# 等待启动
sleep 3

# 检查服务状态
if kill -0 $SERVICE_PID 2>/dev/null; then
    echo -e "${GREEN}✅ 服务运行正常${NC}"
    echo -e "${GREEN}🌐 访问地址: http://localhost:8000${NC}"
    echo -e "${GREEN}📚 API文档: http://localhost:8000/docs${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    exit 1
fi
