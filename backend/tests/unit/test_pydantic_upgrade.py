"""
Pydantic v2 升级验证测试
测试主要功能是否兼容 Pydantic v2
"""

import sys
import os

# 添加项目路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def test_pydantic_v2_basic():
    """测试基本的 Pydantic v2 功能"""
    print("🚀 开始 Pydantic v2 基础功能测试...")

    try:
        import pydantic

        print(f"📦 Pydantic 版本: {pydantic.VERSION}")

        from pydantic import BaseModel, ConfigDict
        from typing import Optional
        from datetime import datetime
        import uuid

        # 测试基本模型定义
        class TestUser(BaseModel):
            model_config = ConfigDict(from_attributes=True)

            id: uuid.UUID
            name: str
            email: str
            age: Optional[int] = None
            created_at: datetime

        # 测试模型创建
        test_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Test User",
            "email": "test@example.com",
            "age": 25,
            "created_at": "2024-01-01T00:00:00Z",
        }

        user = TestUser(**test_data)
        print(f"✅ 基本模型创建成功: {user.name}")

        # 测试序列化
        user_dict = user.model_dump()
        print(f"✅ 模型序列化成功: {type(user_dict)}")

        # 测试验证
        user_json = user.model_dump_json()
        print(f"✅ JSON序列化成功: {len(user_json)} 字符")

        # 测试从字典创建
        user2 = TestUser.model_validate(test_data)
        print(f"✅ model_validate 创建成功: {user2.email}")

        return True

    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False


def test_with_sqlalchemy_mock():
    """测试与 SQLAlchemy 模拟对象的兼容性"""
    print("\n🔧 测试 SQLAlchemy 兼容性...")

    try:
        from pydantic import BaseModel, ConfigDict
        from datetime import datetime
        import uuid

        # 模拟 SQLAlchemy 对象
        class MockSQLAlchemyUser:
            def __init__(self):
                self.id = uuid.uuid4()
                self.name = "Mock User"
                self.email = "mock@example.com"
                self.created_at = datetime.now()

        # Pydantic v2 模型
        class UserRead(BaseModel):
            model_config = ConfigDict(from_attributes=True)

            id: uuid.UUID
            name: str
            email: str
            created_at: datetime

        # 测试从 ORM 对象创建
        mock_user = MockSQLAlchemyUser()
        user_pydantic = UserRead.model_validate(mock_user)

        print(f"✅ ORM 对象转换成功: {user_pydantic.name}")
        print(f"✅ 兼容性测试通过")

        return True

    except Exception as e:
        print(f"❌ SQLAlchemy 兼容性测试失败: {e}")
        return False


def test_category_schema_upgrade():
    """测试分类 Schema 的升级兼容性"""
    print("\n📁 测试分类 Schema 升级...")

    try:
        from pydantic import BaseModel, ConfigDict
        from typing import Optional, List
        from datetime import datetime
        import uuid
        from enum import Enum

        # 模拟事务类型枚举
        class TransactionTypeEnum(str, Enum):
            INCOME = "income"
            EXPENSE = "expense"
            TRANSFER = "transfer"

        # 升级后的分类 Schema
        class CategoryBase(BaseModel):
            name: str
            type: TransactionTypeEnum
            icon: Optional[str] = None
            color: Optional[str] = None
            parent_id: Optional[uuid.UUID] = None

        class CategoryRead(CategoryBase):
            model_config = ConfigDict(from_attributes=True)

            id: uuid.UUID
            user_id: uuid.UUID
            is_system: bool
            created_at: datetime
            updated_at: datetime
            children: Optional[List["CategoryRead"]] = []

        # 测试创建
        test_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "name": "测试分类",
            "type": TransactionTypeEnum.EXPENSE,
            "icon": "🧪",
            "color": "#FF5722",
            "parent_id": None,
            "is_system": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "children": [],
        }

        category = CategoryRead(**test_data)
        print(f"✅ 分类 Schema 创建成功: {category.name}")

        # 测试序列化
        category_dict = category.model_dump()
        print(f"✅ 分类序列化成功: {category_dict['type']}")

        return True

    except Exception as e:
        print(f"❌ 分类 Schema 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Pydantic v2 最小可行性测试")
    print("=" * 60)

    # 首先检查当前版本
    try:
        import pydantic

        current_version = pydantic.VERSION
        print(f"当前 Pydantic 版本: {current_version}")

        if current_version.startswith("1."):
            print("⚠️ 当前使用 Pydantic v1，请先升级到 v2")
            print("运行命令: pip install 'pydantic>=2.0'")
            sys.exit(1)

    except ImportError:
        print("❌ 无法导入 Pydantic，请安装")
        sys.exit(1)

    # 运行测试
    tests = [
        test_pydantic_v2_basic,
        test_with_sqlalchemy_mock,
        test_category_schema_upgrade,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过，可以进行 Pydantic v2 升级！")
        sys.exit(0)
    else:
        print("❌ 测试失败，需要修复问题后再升级")
        sys.exit(1)
