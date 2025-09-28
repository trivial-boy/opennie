#!/usr/bin/env python3
"""
检查数据库表结构
"""

import asyncio
from app.core.database import db, init_database
from sqlalchemy import text


async def check_database():
    """检查数据库状态"""
    # 初始化数据库连接
    await init_database()

    async with db.engine.begin() as conn:
        # 检查现有表
        result = await conn.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        )
        tables = [row[0] for row in result.fetchall()]

        print("当前数据库中的表:")
        for table in tables:
            print(f"  - {table}")

        # 检查是否有accounts表
        if "accounts" not in tables:
            print("\n❌ accounts表不存在")
        else:
            print("\n✅ accounts表存在")

        # 检查是否有bills表
        if "bills" not in tables:
            print("❌ bills表不存在")
        else:
            print("✅ bills表存在")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(check_database())
