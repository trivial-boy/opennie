#!/usr/bin/env python3
"""
简单测试SQL执行功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.core.database import db
from sqlalchemy import text


async def test_sql_execution():
    """测试SQL执行功能"""
    print("🧪 测试SQL执行功能")
    print("=" * 60)

    # 连接数据库
    await db.connect()

    # 创建数据库会话
    async with db.get_session() as session:
        try:
            # 测试基础查询
            print("📋 执行基础SQL查询")

            # 查询用户表
            result = await session.execute(
                text("SELECT id, username, email FROM users LIMIT 3")
            )
            rows = result.fetchall()
            columns = list(result.keys())

            print(f"✅ 查询成功，返回 {len(rows)} 行数据")
            print(f"列名: {columns}")

            # 转换为字典格式
            data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    row_dict[column] = row[i]
                data.append(row_dict)

            print("数据示例:")
            for i, item in enumerate(data):
                print(f"  {i + 1}. {item}")

            print("\n✅ SQL执行功能测试成功！")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_sql_execution())
