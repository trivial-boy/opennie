# 🚀 阿里云服务器部署指南

## 📋 部署概览

本项目支持一键部署到阿里云ECS服务器，使用Docker Compose编排多个服务容器。

### 🏗️ 架构组成
- **Nginx**: 反向代理和SSL终端
- **FastAPI**: Python后端API服务
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话存储

---

## 🛠️ 服务器准备

### 1. 阿里云ECS配置要求
```
CPU: 2核心
内存: 4GB
磁盘: 40GB SSD
网络: 公网IP + 5Mbps带宽
操作系统: Ubuntu 20.04/22.04 LTS
```

### 2. 安全组配置
在阿里云控制台配置安全组规则：
```
入方向规则:
- SSH: 22/TCP (源: 0.0.0.0/0 或特定IP)
- HTTP: 80/TCP (源: 0.0.0.0/0)
- HTTPS: 443/TCP (源: 0.0.0.0/0)
- API: 8000/TCP (源: 0.0.0.0/0，可选)
```

### 3. 域名解析
在域名服务商添加DNS记录：
```
类型: A记录
主机记录: @ (或 www)
记录值: 您的服务器公网IP
TTL: 600
```

---

## 🚀 一键部署

### 方式一：自动部署脚本（推荐）

1. **连接服务器**
```bash
ssh root@your-server-ip
```

2. **下载部署文件**
```bash
git clone https://github.com/your-username/vibecoding.git
cd vibecoding
```

3. **运行部署脚本**
```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动：
- ✅ 安装Docker和Docker Compose
- ✅ 配置防火墙规则
- ✅ 生成安全密码
- ✅ 配置SSL证书
- ✅ 构建和启动所有服务

### 方式二：手动部署

1. **安装依赖**
```bash
# 安装Docker
curl -fsSL https://get.docker.com | bash
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **配置环境变量**
```bash
cp .env.production .env
# 编辑 .env 文件，修改密码和域名
nano .env
```

3. **申请SSL证书**
```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
```

4. **启动服务**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📊 部署验证

### 检查服务状态
```bash
# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 健康检查
curl https://your-domain.com/health
```

### 预期响应
```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "database": "postgresql"
    },
    "redis": "connected"
  },
  "environment": "production"
}
```

---

## 🔧 运维管理

### 常用命令
```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 更新应用
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# 查看数据库
docker-compose -f docker-compose.prod.yml exec db psql -U vibecoding_user -d vibecoding

# 备份数据库
docker-compose -f docker-compose.prod.yml exec db pg_dump -U vibecoding_user vibecoding > backup.sql
```

### 日志查看
```bash
# API服务日志
docker-compose -f docker-compose.prod.yml logs -f api

# 数据库日志
docker-compose -f docker-compose.prod.yml logs -f db

# Nginx日志
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 监控指标
```bash
# 容器资源使用
docker stats

# 磁盘使用
df -h

# 内存使用
free -h

# 系统负载
top
```

---

## 🔒 安全配置

### 1. SSL证书自动续期
```bash
# 添加定时任务
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 2. 防火墙加固
```bash
# 限制SSH访问（可选）
sudo ufw limit ssh

# 启用fail2ban（可选）
sudo apt-get install fail2ban
```

### 3. 定期备份
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U vibecoding_user vibecoding > backup_$DATE.sql
gzip backup_$DATE.sql
# 上传到阿里云OSS或其他存储
EOF

chmod +x backup.sh
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

---

## 🐛 故障排除

### 常见问题

**1. 端口占用**
```bash
# 查看端口占用
sudo netstat -tlnp | grep :80
sudo lsof -i :80

# 停止占用进程
sudo systemctl stop apache2  # 或其他服务
```

**2. SSL证书问题**
```bash
# 检查证书有效性
openssl x509 -in ssl/cert.pem -text -noout

# 重新申请证书
sudo certbot certonly --standalone -d your-domain.com --force-renewal
```

**3. 数据库连接失败**
```bash
# 检查数据库容器
docker-compose -f docker-compose.prod.yml logs db

# 手动连接测试
docker-compose -f docker-compose.prod.yml exec db psql -U vibecoding_user -d vibecoding
```

**4. 内存不足**
```bash
# 增加swap空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📈 性能优化

### 1. 数据库优化
```sql
-- 在数据库中执行
-- 创建索引
CREATE INDEX CONCURRENTLY idx_bills_user_date ON bills(user_id, date);
CREATE INDEX CONCURRENTLY idx_bills_category_date ON bills(category_id, date);

-- 分析表统计信息
ANALYZE;
```

### 2. Redis缓存配置
```bash
# 编辑Redis配置
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. Nginx优化
根据访问量调整worker进程数和连接数限制。

---

## 🆘 技术支持

如果在部署过程中遇到问题：

1. 📧 发送邮件到: support@example.com
2. 📱 查看项目Issues: https://github.com/your-username/vibecoding/issues
3. 📚 参考API文档: https://your-domain.com/docs

---

## 📝 更新日志

- **v1.0.0**: 初始部署版本，支持基础记账功能
- **v1.1.0**: 新增预算管理和资产管理功能
- **v1.2.0**: 优化性能和安全配置

---

**🎉 恭喜！您的记账App已成功部署到阿里云！**