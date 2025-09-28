#!/usr/bin/env python3
"""
检查测试用户信息
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


async def check_test_user():
    """检查测试用户信息"""
    # 从环境变量获取数据库连接信息
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("❌ 数据库连接URL未找到")
        return

    try:
        # 连接数据库
        conn = await asyncpg.connect(DATABASE_URL)

        # 查询用户信息
        users = await conn.fetch(
            "SELECT id, username, email, email_verified FROM users"
        )

        print(f"📋 找到 {len(users)} 个用户:")
        for user in users:
            print(f"  - ID: {user['id']}")
            print(f"    用户名: {user['username']}")
            print(f"    邮箱: {user['email']}")
            print(f"    邮箱已验证: {user['email_verified']}")
            print()

        await conn.close()

    except Exception as e:
        print(f"❌ 检查用户失败: {e}")


if __name__ == "__main__":
    asyncio.run(check_test_user())
