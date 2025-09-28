#!/usr/bin/env python3
"""
直接测试预算数据库操作
"""

import asyncio
import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import uuid

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db
from app.models.budget import Budget, BudgetCategory, PeriodTypeEnum
from app.models.account import Account
from app.models.category import Category
from app.models.user import User
from sqlalchemy import select


async def test_budget_db():
    """直接测试预算数据库操作"""
    print("🔍 直接测试预算数据库操作...")

    # 连接数据库
    await db.connect()

    try:
        async with db.get_session() as session:
            # 1. 查找指定的测试用户
            user_stmt = select(User).where(User.email == "test_uswxfh@example.com")
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                print("❌ 没有找到用户")
                return

            print(f"✅ 找到用户: {user.username} (ID: {user.id})")

            # 2. 查找该用户的账本
            account_stmt = select(Account).where(Account.user_id == user.id).limit(1)
            account_result = await session.execute(account_stmt)
            account = account_result.scalar_one_or_none()

            if not account:
                print("❌ 没有找到账本")
                return

            print(f"✅ 找到账本: {account.name} (ID: {account.id})")

            # 3. 查找该用户的分类
            category_stmt = (
                select(Category)
                .where((Category.user_id == user.id) & (Category.type == "EXPENSE"))
                .limit(2)
            )
            category_result = await session.execute(category_stmt)
            categories = category_result.scalars().all()

            if len(categories) < 1:
                print("❌ 没有找到分类")
                return

            print(f"✅ 找到 {len(categories)} 个分类")
            for cat in categories:
                print(f"   - {cat.name} (ID: {cat.id})")

            # 4. 创建预算
            print("\n📝 创建预算...")
            start_date = date.today()
            end_date = start_date + timedelta(days=30)

            budget = Budget(
                user_id=user.id,
                account_id=account.id,
                name="数据库测试预算",
                total_amount=Decimal("3000.00"),
                period_type=PeriodTypeEnum.MONTHLY,
                start_date=start_date,
                end_date=end_date,
            )

            session.add(budget)
            await session.flush()  # 获取预算ID

            print(f"✅ 预算创建成功: {budget.name} (ID: {budget.id})")

            # 5. 创建预算分类明细
            if categories:
                print("📝 创建预算分类明细...")

                budget_category = BudgetCategory(
                    budget_id=budget.id,
                    category_id=categories[0].id,
                    allocated_amount=Decimal("1500.00"),
                )

                session.add(budget_category)
                print(f"✅ 预算分类明细创建成功: {categories[0].name}")

            # 6. 提交事务
            await session.commit()
            print("✅ 事务提交成功")

            # 7. 查询创建的预算
            print("\n🔍 查询创建的预算...")
            query_stmt = select(Budget).where(Budget.id == budget.id)
            query_result = await session.execute(query_stmt)
            queried_budget = query_result.scalar_one_or_none()

            if queried_budget:
                print(f"✅ 预算查询成功:")
                print(f"   - 名称: {queried_budget.name}")
                print(f"   - 总金额: {queried_budget.total_amount}")
                print(f"   - 周期类型: {queried_budget.period_type}")
                print(f"   - 开始日期: {queried_budget.start_date}")
                print(f"   - 结束日期: {queried_budget.end_date}")

            # 8. 清理测试数据
            print("\n🧹 清理测试数据...")

            # 删除预算分类明细
            category_delete_stmt = select(BudgetCategory).where(
                BudgetCategory.budget_id == budget.id
            )
            category_delete_result = await session.execute(category_delete_stmt)
            categories_to_delete = category_delete_result.scalars().all()

            for cat in categories_to_delete:
                await session.delete(cat)

            # 删除预算
            await session.delete(queried_budget)
            await session.commit()

            print("✅ 测试数据清理完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_budget_db())
