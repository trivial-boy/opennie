#!/usr/bin/env python3
"""
检查数据库中的用户
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import db


async def check_users():
    """检查数据库中的用户"""
    print("🔍 检查数据库用户...")

    # 连接数据库
    await db.connect()

    try:
        async with db.engine.begin() as conn:
            # 先查看表结构
            columns_result = await conn.execute(
                text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            )

            columns = columns_result.fetchall()
            print("用户表结构:")
            for col in columns:
                print(f"   - {col.column_name}: {col.data_type}")

            # 查询用户
            result = await conn.execute(
                text("""
                SELECT id, username, email, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            """)
            )

            users = result.fetchall()

            if not users:
                print("❌ 数据库中没有用户")
                return

            print(f"✅ 找到 {len(users)} 个用户:")
            for user in users:
                print(f"   - {user.username} ({user.email})")

    except Exception as e:
        print(f"❌ 查询用户失败: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(check_users())
