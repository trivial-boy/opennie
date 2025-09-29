#!/usr/bin/env python3
"""
测试SQL执行API的脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.core.database import db
from app.services.sql_executor import SQLExecutorService


async def test_sql_executor():
    """测试SQL执行服务"""
    print("🧪 测试SQL执行服务")
    print("=" * 60)

    # 连接数据库
    await db.connect()

    # 创建数据库会话
    async with db.get_session() as session:
        try:
            # 测试1: 验证SQL
            print("📋 测试1: SQL验证")
            test_sqls = [
                "SELECT * FROM users LIMIT 10",
                "DROP TABLE users",
                "SELECT COUNT(*) FROM categories",
                "INSERT INTO test VALUES (1)",
                "SHOW TABLES",
            ]

            for sql in test_sqls:
                is_valid, is_safe, sql_type, error = SQLExecutorService.validate_sql(
                    sql
                )
                print(f"SQL: {sql}")
                print(f"  ✅ 有效: {is_valid}, 安全: {is_safe}, 类型: {sql_type}")
                if error:
                    print(f"  ❌ 错误: {error}")
                print()

            # 测试2: 执行安全SQL查询
            print("📋 测试2: 执行安全SQL查询")

            # 查询用户表
            result = await SQLExecutorService.execute_sql(
                session=session,
                sql="SELECT id, username, email, created_at FROM users LIMIT 5",
                limit=10,
                safe_mode=True,
            )

            print("查询用户表结果:")
            print(f"  成功: {result['success']}")
            print(f"  行数: {result['rows_affected']}")
            print(f"  列名: {result['columns']}")
            print(f"  耗时: {result['execution_time']:.3f}s")

            if result["data"]:
                print("  数据预览:")
                for i, row in enumerate(result["data"][:3]):
                    print(f"    {i + 1}. {row}")

            print()

            # 查询分类表
            result2 = await SQLExecutorService.execute_sql(
                session=session,
                sql="SELECT id, name, type, is_system FROM categories LIMIT 5",
                limit=10,
                safe_mode=True,
            )

            print("查询分类表结果:")
            print(f"  成功: {result2['success']}")
            print(f"  行数: {result2['rows_affected']}")
            print(f"  列名: {result2['columns']}")

            if result2["data"]:
                print("  数据预览:")
                for i, row in enumerate(result2["data"][:3]):
                    print(f"    {i + 1}. {row}")

            print()

            # 测试3: 尝试执行危险SQL（应该被阻止）
            print("📋 测试3: 尝试执行危险SQL")

            dangerous_result = await SQLExecutorService.execute_sql(
                session=session, sql="DELETE FROM users WHERE id = 999", safe_mode=True
            )

            print("危险SQL执行结果:")
            print(f"  成功: {dangerous_result['success']}")
            print(f"  错误信息: {dangerous_result['error_message']}")

            print("\n✅ SQL执行服务测试完成！")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(test_sql_executor())
