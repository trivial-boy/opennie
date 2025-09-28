#!/usr/bin/env python3
"""
检查预算相关数据库表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import db


async def check_budget_tables():
    """检查预算相关表"""
    print("🔍 检查预算相关数据库表...")

    # 连接数据库
    await db.connect()

    try:
        async with db.engine.begin() as conn:
            # 查询所有表
            result = await conn.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            )

            tables = [row[0] for row in result.fetchall()]

            print(f"✅ 数据库中的所有表:")
            for table in tables:
                print(f"   - {table}")

            # 检查预算相关表
            budget_tables = ["budgets", "budget_categories"]
            print(f"\n🔍 检查预算相关表:")

            for table_name in budget_tables:
                if table_name in tables:
                    print(f"   ✅ {table_name} - 存在")

                    # 查看表结构
                    columns_result = await conn.execute(
                        text(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)
                    )

                    columns = columns_result.fetchall()
                    print(f"      表结构:")
                    for col in columns:
                        print(
                            f"        - {col.column_name}: {col.data_type} ({col.is_nullable})"
                        )
                else:
                    print(f"   ❌ {table_name} - 不存在")

    except Exception as e:
        print(f"❌ 检查表失败: {e}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(check_budget_tables())
