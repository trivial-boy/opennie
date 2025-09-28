#!/usr/bin/env python3
"""
直接测试账本创建
"""

import asyncio
from app.core.database import init_database, db
from app.models.user import User
from app.models.account import Account
from app.schemas.account import AccountCreate
from sqlalchemy import select


async def test_account_creation():
    """直接测试账本创建"""
    await init_database()

    async with db.get_session() as session:
        # 查找测试用户
        stmt = select(User).where(User.email == "testaccounts@example.com")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print("❌ 测试用户不存在")
            return

        print(f"✅ 找到测试用户: {user.username} ({user.id})")

        # 创建账本数据
        account_data = AccountCreate(
            name="测试账本",
            description="这是一个测试账本",
            currency="CNY",
            is_shared=False,
            members=[],
        )

        try:
            # 创建账本
            account = Account(user_id=user.id, **account_data.dict())

            session.add(account)
            await session.commit()
            await session.refresh(account)

            print(f"✅ 账本创建成功: {account.name} (ID: {account.id})")

        except Exception as e:
            print(f"❌ 账本创建失败: {e}")
            await session.rollback()

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_account_creation())
