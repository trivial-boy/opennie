# 开发指南

## 🚀 快速开发工具

为了提高开发效率，项目提供了多个便捷的开发脚本：

### 📋 脚本总览

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `./dev-tools.sh` | 🛠️ 开发者工具集 | 日常开发的万能工具 |
| `./restart-app.sh` | 🔄 快速重启app | 本地修改代码后快速重启 |
| `./redeploy.sh` | 📥 代码同步重部署 | 拉取远程代码并重新部署 |
| `./deploy.sh` | 🚀 完整部署 | 首次部署或完整重建 |

---

## 🛠️ 开发者工具 (dev-tools.sh)

**一站式开发工具，提供所有常用功能**

```bash
./dev-tools.sh [选项]
```

### 可用选项：

| 选项 | 功能 | 描述 |
|------|------|------|
| `restart` | 🔄 快速重启 | 重启app容器，保持其他服务运行 |
| `redeploy` | 📥 代码同步重部署 | 拉取最新代码并重新部署 |
| `logs` | 📋 实时日志 | 查看app容器实时日志 |
| `status` | 📊 服务状态 | 查看所有服务状态和资源使用 |
| `shell` | 🐚 进入容器 | 进入app容器的bash shell |
| `clean` | 🧹 清理资源 | 清理Docker未使用的资源 |
| `health` | 🏥 健康检查 | 检查应用和依赖服务状态 |
| `help` | ❓ 帮助信息 | 显示所有可用选项 |

### 使用示例：

```bash
# 查看帮助
./dev-tools.sh help

# 快速重启（最常用）
./dev-tools.sh restart

# 拉取代码并重部署
./dev-tools.sh redeploy

# 查看实时日志
./dev-tools.sh logs

# 检查应用状态
./dev-tools.sh health

# 进入容器调试
./dev-tools.sh shell
```

---

## 🔄 快速重启 (restart-app.sh)

**适用场景：本地修改代码后需要快速重启app服务**

```bash
./restart-app.sh
```

### 执行步骤：
1. 🛑 停止app容器
2. 🔨 重新构建app镜像
3. 🚀 启动app容器
4. ✅ 验证服务状态

### 特点：
- ⚡ 速度快：只重启app，不影响MySQL和Redis
- 🔍 自动健康检查
- 📋 显示服务访问地址

---

## 📥 代码同步重部署 (redeploy.sh)

**适用场景：拉取远程代码更新并重新部署**

```bash
./redeploy.sh
```

### 执行步骤：
1. 📋 检查Git状态
2. 💾 提示提交未保存的更改（可选）
3. 📥 拉取最新代码
4. 🛑 停止app容器
5. 🔨 重新构建app镜像（无缓存）
6. 🚀 启动app容器
7. ✅ 验证服务状态

### 特点：
- 🔄 智能Git管理：自动检查和拉取代码
- 🚫 无缓存构建：确保使用最新代码
- 📋 显示提交历史
- 🏥 完整健康检查

---

## 🚀 完整部署 (deploy.sh)

**适用场景：首次部署或需要重建所有服务**

```bash
./deploy.sh
```

### 执行步骤：
1. 🔍 检查Docker镜像加速配置
2. 📁 创建必要目录
3. 🛑 停止所有现有服务
4. �� 构建并启动所有服务
5. ⏳ 等待服务启动
6. ✅ 验证所有服务状态

---

## 💻 日常开发流程

### 场景1：本地修改代码
```bash
# 修改代码后
./dev-tools.sh restart
# 或
./restart-app.sh
```

### 场景2：拉取远程更新
```bash
# 拉取远程代码并部署
./dev-tools.sh redeploy
# 或
./redeploy.sh
```

### 场景3：查看问题
```bash
# 查看实时日志
./dev-tools.sh logs

# 检查服务状态
./dev-tools.sh status

# 健康检查
./dev-tools.sh health

# 进入容器调试
./dev-tools.sh shell
```

### 场景4：清理资源
```bash
# 清理Docker资源
./dev-tools.sh clean
```

---

## 🔍 故障排除

### 应用启动失败
```bash
# 1. 查看日志
./dev-tools.sh logs

# 2. 检查状态
./dev-tools.sh status

# 3. 健康检查
./dev-tools.sh health

# 4. 进入容器调试
./dev-tools.sh shell
```

### 依赖安装失败
```bash
# 进入容器手动安装
./dev-tools.sh shell
pip3 install -r requirements.txt
```

### 数据库连接失败
```bash
# 检查MySQL容器状态
docker-compose ps mysql

# 查看MySQL日志
docker-compose logs mysql
```

---

## 📊 监控和调试

### 实时监控
```bash
# 查看所有服务状态
./dev-tools.sh status

# 查看app实时日志
./dev-tools.sh logs

# Docker资源使用
docker stats
```

### 性能分析
```bash
# 容器资源使用
docker stats --no-stream

# 磁盘使用
docker system df

# 网络连接
docker network ls
```

---

## 🎯 最佳实践

1. **开发前检查**：使用 `./dev-tools.sh health` 确保环境正常
2. **频繁重启**：使用 `./dev-tools.sh restart` 而不是完整重建
3. **代码同步**：使用 `./dev-tools.sh redeploy` 获取最新代码
4. **问题调试**：使用 `./dev-tools.sh logs` 和 `./dev-tools.sh shell`
5. **资源清理**：定期使用 `./dev-tools.sh clean` 清理无用资源

---

## 🌐 访问地址

部署成功后，可通过以下地址访问：

- **本地访问**: http://localhost:8000
- **内网访问**: http://172.16.2.50:8000  
- **API文档**: http://172.16.2.50:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 🆘 获取帮助

```bash
# 查看开发工具帮助
./dev-tools.sh help

# 查看部署帮助
./deploy.sh --help

# 查看项目文档
cat README-Docker.md
```