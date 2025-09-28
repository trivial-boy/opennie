#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db
from app.models.user import User
from app.core.security import get_password_hash


async def create_test_user():
    """创建测试用户"""
    try:
        # 连接数据库
        await db.connect()

        # 创建测试用户
        async with db.get_session() as session:
            # 检查用户是否已存在
            from sqlalchemy import select

            stmt = select(User).where(User.email == "test@example.com")
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("测试用户已存在，删除后重新创建...")
                await session.delete(existing_user)
                await session.commit()

            # 创建新的测试用户 - 使用预生成的bcrypt哈希避免bcrypt初始化问题
            # 这是 'testpassword123' 的bcrypt哈希
            password_hash = (
                "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4hJRr6HlvG"
            )

            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash=password_hash,
                email_verified=True,
                email_verified_at=datetime.utcnow(),
            )

            session.add(test_user)
            await session.commit()

            print(f"✅ 测试用户创建成功:")
            print(f"   用户名: {test_user.username}")
            print(f"   邮箱: {test_user.email}")
            print(f"   ID: {test_user.id}")
            print(f"   邮箱已验证: {test_user.email_verified}")

    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(create_test_user())
