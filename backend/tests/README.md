# 测试文件组织结构

本项目的测试文件已按照标准测试分层结构进行组织：

## 目录结构

```
tests/
├── __init__.py
├── README.md
├── unit/                       # 单元测试
│   ├── __init__.py
│   ├── test_user_register.py   # 用户注册相关单元测试
│   ├── test_account_creation.py # 账本创建单元测试
│   └── test_pydantic_upgrade.py # Pydantic升级测试
├── integration/                # 集成测试
│   ├── __init__.py
│   ├── test_auth_api.py        # 用户认证API集成测试
│   ├── test_categories_api.py  # 分类管理API集成测试
│   ├── test_login_simple.py    # 简单登录测试
│   ├── test_register_simple.py # 简单注册测试
│   └── test_accounts_bills_api.py # 账本和账单API测试
└── e2e/                        # 端到端测试
    └── __init__.py
```

## 测试类型说明

### 单元测试 (unit/)
- 测试单个函数、类或模块的功能
- 不依赖外部服务（数据库、网络等）
- 运行速度快，适合频繁执行

### 集成测试 (integration/)
- 测试多个组件之间的交互
- 可能依赖数据库、Redis等外部服务
- 验证API端点的完整功能

### 端到端测试 (e2e/)
- 测试完整的用户场景
- 从用户界面到后端的完整流程
- 模拟真实用户操作

## 运行测试

### 运行单元测试
```bash
# 运行所有单元测试
python3 -m pytest tests/unit/ -v

# 运行特定单元测试
python3 tests/unit/test_user_register.py
```

### 运行集成测试
```bash
# 运行所有集成测试
python3 -m pytest tests/integration/ -v

# 运行特定集成测试
python3 tests/integration/test_auth_api.py
```

### 运行所有测试
```bash
python3 -m pytest tests/ -v
```

## 测试文件说明

### 单元测试文件

- **test_user_register.py**: 测试密码哈希、用户模型、Pydantic schemas
- **test_account_creation.py**: 测试账本创建逻辑
- **test_pydantic_upgrade.py**: 验证Pydantic v2升级的兼容性

### 集成测试文件

- **test_auth_api.py**: 完整的用户认证流程测试（注册、登录、刷新token、登出）
- **test_categories_api.py**: 分类管理的CRUD操作测试
- **test_login_simple.py**: 简单的登录功能测试
- **test_register_simple.py**: 简单的注册功能测试
- **test_accounts_bills_api.py**: 账本和账单管理API测试

## 测试最佳实践

1. **导入路径**: 所有测试文件都使用相对于项目根目录的导入路径
2. **独立性**: 每个测试都应该能够独立运行
3. **清理**: 测试后应清理创建的测试数据
4. **命名**: 测试文件以 `test_` 开头，测试函数以 `test_` 开头
5. **文档**: 每个测试文件都应包含清晰的文档说明

## 注意事项

- 运行集成测试前确保后端服务正在运行
- 某些测试可能需要特定的数据库状态
- 测试用户数据会在每次运行时动态生成，避免冲突