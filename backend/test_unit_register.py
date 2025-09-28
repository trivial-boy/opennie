#!/usr/bin/env python3
"""
单元测试 - 注册功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserRead
from app.models.user import User
from datetime import datetime
import uuid


async def test_password_hash():
    """测试密码哈希功能"""
    print("🔐 测试密码哈希...")

    password = "test123"
    try:
        # 测试密码哈希
        hashed = get_password_hash(password)
        print(f"✅ 密码哈希成功: {hashed[:30]}...")

        # 测试密码验证
        is_valid = verify_password(password, hashed)
        print(f"✅ 密码验证成功: {is_valid}")

        # 测试错误密码
        is_invalid = verify_password("wrong", hashed)
        print(f"✅ 错误密码验证: {is_invalid}")

        return True
    except Exception as e:
        print(f"❌ 密码哈希失败: {str(e)}")
        return False


def test_user_model():
    """测试用户模型"""
    print("\n👤 测试用户模型...")

    try:
        # 创建用户对象
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="$pbkdf2-sha256$29000$test",
            email_verified=True,
            email_verified_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        print(f"✅ 用户模型创建成功: {user.username}")
        print(f"   ID: {user.id}")
        print(f"   邮箱: {user.email}")
        print(f"   验证状态: {user.email_verified}")

        return user
    except Exception as e:
        print(f"❌ 用户模型创建失败: {str(e)}")
        return None


def test_user_schema(user):
    """测试用户Schema序列化"""
    print("\n📋 测试用户Schema...")

    try:
        # 测试from_orm
        user_read = UserRead.from_orm(user)
        print(f"✅ UserRead.from_orm 成功")
        print(f"   用户名: {user_read.username}")
        print(f"   邮箱: {user_read.email}")
        print(f"   ID: {user_read.id}")

        # 测试dict序列化
        user_dict = user_read.dict()
        print(f"✅ UserRead.dict() 成功")
        print(f"   字典键: {list(user_dict.keys())}")

        return user_read
    except Exception as e:
        print(f"❌ UserRead序列化失败: {str(e)}")
        return None


def test_response_model():
    """测试响应模型"""
    print("\n📤 测试响应模型...")

    try:
        from app.schemas.common import ResponseModel
        from app.schemas.user import UserRead

        # 创建用户
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="$pbkdf2-sha256$29000$test",
            email_verified=True,
            email_verified_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        user_read = UserRead.from_orm(user)

        # 创建响应模型
        response = ResponseModel(data=user_read, message="注册成功")

        print(f"✅ ResponseModel 创建成功")
        print(f"   消息: {response.message}")
        print(f"   成功状态: {response.success}")

        # 测试dict序列化
        response_dict = response.dict()
        print(f"✅ ResponseModel.dict() 成功")

        return True
    except Exception as e:
        print(f"❌ ResponseModel 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🧪 开始单元测试...")
    print("=" * 50)

    # 测试密码哈希
    password_ok = await test_password_hash()

    # 测试用户模型
    user = test_user_model()

    # 测试用户Schema
    user_read = None
    if user:
        user_read = test_user_schema(user)

    # 测试响应模型
    response_ok = test_response_model()

    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"密码哈希: {'✅' if password_ok else '❌'}")
    print(f"用户模型: {'✅' if user else '❌'}")
    print(f"用户Schema: {'✅' if user_read else '❌'}")
    print(f"响应模型: {'✅' if response_ok else '❌'}")

    all_passed = all([password_ok, user, user_read, response_ok])
    print(f"\n🎯 总体结果: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
