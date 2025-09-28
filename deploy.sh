#!/bin/bash

# 阿里云服务器部署脚本
# 使用方法: bash deploy.sh

set -e

echo "🚀 开始部署记账App到阿里云服务器..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker和Docker Compose
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，正在安装...${NC}"
        # 安装Docker
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

# 配置防火墙
setup_firewall() {
    echo -e "${YELLOW}📝 配置防火墙...${NC}"

    # 检查是否为阿里云ECS (通过检查元数据)
    if curl -s --max-time 3 http://100.100.100.200/latest/meta-data/instance-id &>/dev/null; then
        echo -e "${YELLOW}⚠️  检测到阿里云ECS，请在控制台安全组中开放以下端口：${NC}"
        echo "   - 22 (SSH)"
        echo "   - 80 (HTTP)"
        echo "   - 443 (HTTPS)"
        echo "   - 8000 (API，可选)"
        read -p "已配置安全组？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ 请先配置安全组后再继续${NC}"
            exit 1
        fi
    fi

    # 配置系统防火墙
    if command -v ufw &> /dev/null; then
        sudo ufw allow 22
        sudo ufw allow 80
        sudo ufw allow 443
        sudo ufw --force enable
        echo -e "${GREEN}✅ UFW 防火墙配置完成${NC}"
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=22/tcp
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --permanent --add-port=443/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}✅ firewalld 防火墙配置完成${NC}"
    fi
}

# 生成SSL证书 (使用Let's Encrypt)
setup_ssl() {
    read -p "请输入您的域名 (例如: example.com): " DOMAIN

    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}❌ 域名不能为空${NC}"
        exit 1
    fi

    # 更新配置文件中的域名
    sed -i "s/your-domain.com/$DOMAIN/g" nginx/conf.d/default.conf
    sed -i "s/DOMAIN=your-domain.com/DOMAIN=$DOMAIN/g" .env.production

    echo -e "${YELLOW}📝 配置SSL证书...${NC}"

    # 安装certbot
    if ! command -v certbot &> /dev/null; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot
        fi
    fi

    # 创建SSL目录
    mkdir -p ssl

    echo -e "${YELLOW}⚠️  SSL证书配置：${NC}"
    echo "1. 确保域名已解析到此服务器IP"
    echo "2. 暂时停止可能占用80端口的服务"
    echo "3. 运行: sudo certbot certonly --standalone -d $DOMAIN"
    echo "4. 复制证书到 ssl/ 目录"
    echo ""
    echo "证书路径通常在: /etc/letsencrypt/live/$DOMAIN/"
    echo "复制命令:"
    echo "sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem"
    echo "sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem"
    echo "sudo chown \$USER:\$USER ssl/*.pem"
}

# 生成随机密码
generate_passwords() {
    echo -e "${YELLOW}📝 生成安全密码...${NC}"

    DB_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -base64 64)
    JWT_SECRET=$(openssl rand -base64 64)

    # 更新环境变量文件
    cp .env.production .env
    sed -i "s/your-db-password/$DB_PASSWORD/g" .env
    sed -i "s/your-redis-password/$REDIS_PASSWORD/g" .env
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env
    sed -i "s/your-jwt-secret-key/$JWT_SECRET/g" .env

    echo -e "${GREEN}✅ 密码生成完成${NC}"
}

# 部署应用
deploy_app() {
    echo -e "${YELLOW}📝 构建和启动应用...${NC}"

    # 停止现有容器
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

    # 构建并启动
    docker-compose -f docker-compose.prod.yml up -d --build

    echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
    sleep 30

    # 检查服务状态
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo -e "${GREEN}✅ 应用部署成功！${NC}"
        echo ""
        echo -e "${GREEN}🎉 部署信息：${NC}"
        echo "API地址: https://$DOMAIN/api/v1/"
        echo "健康检查: https://$DOMAIN/health"
        echo "API文档: https://$DOMAIN/docs"
        echo ""
        echo -e "${YELLOW}📝 管理命令：${NC}"
        echo "查看日志: docker-compose -f docker-compose.prod.yml logs -f"
        echo "重启服务: docker-compose -f docker-compose.prod.yml restart"
        echo "停止服务: docker-compose -f docker-compose.prod.yml down"
        echo ""
    else
        echo -e "${RED}❌ 服务启动失败，请检查日志${NC}"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
}

# 主流程
main() {
    echo -e "${GREEN}=== 记账App 阿里云部署脚本 ===${NC}"
    echo ""

    check_docker
    setup_firewall
    setup_ssl
    generate_passwords
    deploy_app

    echo -e "${GREEN}🎉 部署完成！${NC}"
}

# 执行主流程
main
