# 记账App (OpenNie)

一个现代化的个人财务管理应用，支持智能记账、资产管理、预算控制和AI分析。

## 🚀 项目特性

- 📊 **智能记账**: 支持手动输入、图片识别、语音输入
- 💰 **资产管理**: 多币种支持，资产趋势分析
- 📈 **预算控制**: 分类预算管理，超支提醒
- 🤖 **AI分析**: 自然语言查询，智能财务建议
- 👥 **多人协作**: 共享账本，团队记账
- 📱 **跨平台**: 支持Web、移动端

## 🏗️ 技术架构

### 后端
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL + Redis
- **认证**: JWT Token
- **文件存储**: MinIO/AWS S3
- **AI集成**: Dify工作流

### 前端
- **移动端**: Flutter/React Native
- **桌面端**: Electron + React
- **状态管理**: Provider/Redux

## 📋 项目文档

- [功能设计](./功能设计.md) - 详细功能需求说明
- [技术方案](./技术方案.md) - 完整技术架构设计
- [API文档](./API文档.md) - RESTful API接口规范
- [数据库设计](./database_schema.sql) - 数据库表结构
- [AI协助记录](./AI协助记录.md) - AI开发协助记录

## 🛠️ 开发指南

### 数据库初始化

```bash
# 创建数据库
createdb bill_app

# 初始化表结构
psql -d bill_app -f database_schema.sql

# 如需重置数据库
psql -d bill_app -f reset_database.sql
psql -d bill_app -f database_schema.sql
```

### 后端开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload
```

### 前端开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📊 开发进度

- ✅ 需求分析和设计
- ✅ 技术架构设计
- ✅ 数据库设计
- ✅ API接口设计
- ⏳ 后端代码实现
- ⏳ 前端界面开发
- ⏳ AI功能集成
- ⏳ 测试和部署

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 开源协议

本项目采用 MIT 协议 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

- 项目地址: [https://github.com/trivial-boy/opennie](https://github.com/trivial-boy/opennie)
- 问题反馈: [Issues](https://github.com/trivial-boy/opennie/issues)

---

*由 AI 协助开发 - 让技术为生活服务* 🤖✨