#!/usr/bin/env python3
"""
Add transfer fields to bills table
添加转账字段到账单表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import db
from app.core.config import settings


async def add_transfer_fields():
    """添加转账相关字段到bills表"""
    print("🔧 开始添加转账字段到bills表...")

    # 连接数据库
    await db.connect()

    try:
        async with db.engine.begin() as conn:
            # 检查字段是否已存在
            check_columns = await conn.execute(
                text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'bills'
                AND column_name IN ('to_account_id', 'to_asset_id')
            """)
            )
            existing_columns = [row[0] for row in check_columns.fetchall()]

            if (
                "to_account_id" in existing_columns
                and "to_asset_id" in existing_columns
            ):
                print("✅ 转账字段已存在，无需添加")
                return

            # 添加to_account_id字段
            if "to_account_id" not in existing_columns:
                print("📝 添加 to_account_id 字段...")
                await conn.execute(
                    text("""
                    ALTER TABLE bills
                    ADD COLUMN to_account_id UUID NULL
                """)
                )

                # 添加索引
                await conn.execute(
                    text("""
                    CREATE INDEX IF NOT EXISTS ix_bills_to_account_id
                    ON bills(to_account_id)
                """)
                )
                print("✅ to_account_id 字段添加成功")

            # 添加to_asset_id字段
            if "to_asset_id" not in existing_columns:
                print("📝 添加 to_asset_id 字段...")
                await conn.execute(
                    text("""
                    ALTER TABLE bills
                    ADD COLUMN to_asset_id UUID NULL
                """)
                )

                # 添加索引
                await conn.execute(
                    text("""
                    CREATE INDEX IF NOT EXISTS ix_bills_to_asset_id
                    ON bills(to_asset_id)
                """)
                )
                print("✅ to_asset_id 字段添加成功")

            print("🎉 转账字段添加完成！")

    except Exception as e:
        print(f"❌ 添加转账字段失败: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(add_transfer_fields())
