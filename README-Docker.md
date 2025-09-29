# Docker部署指南

## 快速部署

### 一键部署
```bash
# 克隆代码后，直接运行部署脚本
./deploy.sh
```

### 手动部署
```bash
# 1. 创建必要目录
mkdir -p docker/mysql docker/redis uploads logs

# 2. 启动服务
docker-compose up --build -d

# 3. 检查服务状态
docker-compose ps
docker-compose logs -f app
```

## 配置说明

### 文件结构
```
├── Dockerfile                 # 应用容器配置
├── docker-compose.yml         # 多服务编排
├── docker/
│   ├── .env.docker            # 生产环境变量
│   ├── mysql/
│   │   └── init.sql           # MySQL初始化脚本
│   └── redis/
│       └── redis.conf         # Redis配置文件
├── deploy.sh                  # 一键部署脚本
└── backend/
    └── requirements-docker.txt # Docker部署依赖
```

### 环境配置

#### 数据库配置
- **类型**: MySQL 8.0
- **地址**: mysql:3306
- **数据库**: accounting_db
- **用户**: user
- **密码**: opennie@123

#### Redis配置
- **地址**: redis:6379
- **密码**: opennie@123
- **数据库**: 0

#### 应用配置
- **端口**: 8000
- **健康检查**: /health
- **API文档**: /docs

## 服务管理

### 常用命令
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart app

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f app
docker-compose logs -f mysql
docker-compose logs -f redis

# 进入容器
docker-compose exec app bash
docker-compose exec mysql mysql -u user -p
docker-compose exec redis redis-cli -a "opennie@123"
```

### 数据持久化
- **MySQL数据**: 存储在docker volume `mysql_data`
- **Redis数据**: 存储在docker volume `redis_data`
- **应用上传文件**: 映射到 `./uploads`
- **应用日志**: 映射到 `./logs`

## 性能优化

### Dockerfile优化
- ✅ 使用Python 3.9.6-slim镜像
- ✅ 配置国内镜像源（阿里云、清华大学）
- ✅ 多阶段构建减少镜像大小
- ✅ 非root用户运行提高安全性
- ✅ 健康检查机制

### 数据库优化
- ✅ 连接池配置（10个基础连接，20个溢出）
- ✅ UTF8MB4字符集支持emoji
- ✅ 时区配置（Asia/Shanghai）
- ✅ 索引优化

### Redis优化
- ✅ 持久化配置（RDB + AOF）
- ✅ 内存策略（allkeys-lru）
- ✅ 连接保活
- ✅ 禁用危险命令

## 安全配置

### 应用安全
- ✅ 非root用户运行
- ✅ 生产密钥配置
- ✅ 速率限制
- ✅ CORS配置

### 数据库安全
- ✅ 密码认证
- ✅ 网络隔离
- ✅ 数据持久化

### Redis安全
- ✅ 密码认证
- ✅ 保护模式
- ✅ 危险命令重命名

## 监控检查

### 健康检查
```bash
# 应用健康检查
curl http://localhost:8000/health

# API文档访问
curl http://localhost:8000/docs

# 数据库连接测试
docker-compose exec mysql mysql -u user -p -e "SELECT 1"

# Redis连接测试
docker-compose exec redis redis-cli -a "opennie@123" ping
```

### 服务状态
```bash
# 容器状态
docker-compose ps

# 资源使用
docker stats

# 磁盘使用
docker system df
```

## 故障排除

### 常见问题

#### 端口占用
```bash
# 检查端口占用
lsof -i :8000
lsof -i :3306
lsof -i :6379

# 修改端口（在docker-compose.yml中）
ports:
  - "8001:8000"  # 修改为其他端口
```

#### 数据库连接失败
```bash
# 检查MySQL容器状态
docker-compose logs mysql

# 检查网络连接
docker-compose exec app ping mysql

# 手动连接测试
docker-compose exec mysql mysql -u user -p
```

#### 内存不足
```bash
# 检查系统资源
free -h
df -h

# 调整服务配置
# 在docker-compose.yml中添加内存限制
services:
  app:
    mem_limit: 512m
```

### 日志分析
```bash
# 应用日志
docker-compose logs -f app

# 数据库日志
docker-compose logs -f mysql

# Redis日志
docker-compose logs -f redis

# 系统日志
dmesg | tail
```

## 生产部署建议

### 安全强化
1. 修改默认密码
2. 配置防火墙规则
3. 启用HTTPS
4. 定期安全更新

### 备份策略
1. 数据库定期备份
2. 应用文件备份
3. 配置文件版本控制

### 监控告警
1. 应用性能监控
2. 资源使用监控
3. 错误日志告警
4. 健康检查告警

### 扩展性
1. 负载均衡配置
2. 数据库主从复制
3. Redis集群
4. 容器编排平台（K8s）

## 更新部署

### 应用更新
```bash
# 1. 停止应用容器
docker-compose stop app

# 2. 更新代码
git pull

# 3. 重新构建并启动
docker-compose up --build -d app

# 4. 检查状态
docker-compose logs -f app
```

### 完整更新
```bash
# 1. 停止所有服务
docker-compose down

# 2. 更新代码
git pull

# 3. 重新构建并启动
docker-compose up --build -d

# 4. 检查状态
docker-compose ps
```