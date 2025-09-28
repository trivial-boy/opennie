#!/bin/bash

# 简化版阿里云部署脚本 - 跳过防火墙和SSL配置
# 使用方法: bash deploy-simple.sh

set -e

echo "🚀 开始简化部署记账App..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker和Docker Compose
check_docker() {
    echo -e "${YELLOW}📝 检查Docker环境...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，正在安装...${NC}"
        curl -fsSL https://get.docker.com | bash
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
        echo -e "${GREEN}✅ Docker 安装完成${NC}"
    else
        echo -e "${GREEN}✅ Docker 已安装${NC}"
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，正在安装...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}✅ Docker Compose 安装完成${NC}"
    else
        echo -e "${GREEN}✅ Docker Compose 已安装${NC}"
    fi
}

# 生成配置文件
setup_config() {
    echo -e "${YELLOW}📝 生成配置文件...${NC}"

    # 生成随机密码
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

    # 创建.env文件
    cat > .env << EOF
# 简化部署配置
APP_NAME=振动记账App
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$SECRET_KEY
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql+asyncpg://vibecoding_user:$DB_PASSWORD@db:5432/vibecoding
DB_PASSWORD=$DB_PASSWORD

# Redis配置
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0
REDIS_PASSWORD=$REDIS_PASSWORD

# CORS配置 (允许所有来源，仅用于测试)
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true
ALLOWED_METHODS=*
ALLOWED_HEADERS=*

# JWT配置
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 文件上传配置
MAX_FILE_SIZE=10485760
UPLOAD_PATH=/app/uploads
EOF

    echo -e "${GREEN}✅ 配置文件生成完成${NC}"
}

# 创建简化版docker-compose
create_simple_compose() {
    echo -e "${YELLOW}📝 创建Docker Compose配置...${NC}"

    cat > docker-compose.simple.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    container_name: vibecoding_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: vibecoding
      POSTGRES_USER: vibecoding_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vibecoding_user -d vibecoding"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: vibecoding_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # FastAPI 后端服务
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: vibecoding_api
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend/uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
EOF

    echo -e "${GREEN}✅ Docker Compose 配置创建完成${NC}"
}

# 部署应用
deploy_app() {
    echo -e "${YELLOW}📝 构建和启动应用...${NC}"

    # 停止现有容器
    docker-compose -f docker-compose.simple.yml down 2>/dev/null || true

    # 构建并启动
    docker-compose -f docker-compose.simple.yml up -d --build

    echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
    sleep 30

    # 检查服务状态
    if docker-compose -f docker-compose.simple.yml ps | grep -q "Up"; then
        echo -e "${GREEN}✅ 应用部署成功！${NC}"
        echo ""
        echo -e "${GREEN}🎉 部署信息：${NC}"
        echo "API地址: http://服务器IP:8000/api/v1/"
        echo "健康检查: http://服务器IP:8000/health"
        echo "API文档: http://服务器IP:8000/docs"
        echo ""
        echo -e "${YELLOW}📝 管理命令：${NC}"
        echo "查看日志: docker-compose -f docker-compose.simple.yml logs -f"
        echo "重启服务: docker-compose -f docker-compose.simple.yml restart"
        echo "停止服务: docker-compose -f docker-compose.simple.yml down"
        echo ""
        echo -e "${YELLOW}⚠️  注意事项：${NC}"
        echo "1. 请在阿里云安全组开放8000端口"
        echo "2. 当前使用HTTP，生产环境建议配置HTTPS"
        echo "3. CORS已设置为允许所有来源，请根据需要调整"
    else
        echo -e "${RED}❌ 服务启动失败，请检查日志${NC}"
        docker-compose -f docker-compose.simple.yml logs
        exit 1
    fi
}

# 主流程
main() {
    echo -e "${GREEN}=== 记账App 简化部署脚本 ===${NC}"
    echo -e "${YELLOW}💡 此脚本跳过防火墙和SSL配置，适合快速测试${NC}"
    echo ""

    check_docker
    setup_config
    create_simple_compose
    deploy_app

    echo -e "${GREEN}🎉 简化部署完成！${NC}"
}

# 执行主流程
main
