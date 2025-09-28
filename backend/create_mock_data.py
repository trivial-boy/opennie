#!/usr/bin/env python3
"""
Mock数据生成脚本
创建测试用户和示例数据，包括账本、资产、分类、账单
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_database, db
from app.models.user import User
from app.models.account import Account
from app.models.asset import Asset, AssetTypeEnum
from app.models.category import Category
from app.models.bill import Bill, TransactionTypeEnum
from app.core.security import get_password_hash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


class MockDataGenerator:
    def __init__(self):
        self.user_id = None
        self.account_ids = []
        self.asset_ids = []
        self.category_ids = []

    async def create_test_user(self):
        """创建测试用户"""
        print("🧪 创建测试用户...")

        async with db.get_session() as session:
            # 检查用户是否已存在
            stmt = select(User).where(User.username == "test")
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"ℹ️  用户已存在: test ({existing_user.id})")
                self.user_id = existing_user.id
                return existing_user

            # 创建新用户
            user = User(
                id=uuid.uuid4(),
                username="test",
                email="test@example.com",
                password_hash=get_password_hash("test123"),
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            self.user_id = user.id
            print(f"✅ 用户创建成功: test ({user.id})")
            return user

    async def create_mock_accounts(self):
        """创建示例账本"""
        print("\n📚 创建示例账本...")

        accounts_data = [
            {
                "name": "个人日常账本",
                "description": "记录日常生活收支",
                "currency": "CNY",
                "is_shared": False,
            },
            {
                "name": "家庭共享账本",
                "description": "家庭成员共同记账",
                "currency": "CNY",
                "is_shared": True,
            },
            {
                "name": "投资理财账本",
                "description": "投资收益和理财记录",
                "currency": "CNY",
                "is_shared": False,
            },
        ]

        async with db.get_session() as session:
            for account_data in accounts_data:
                account = Account(
                    id=uuid.uuid4(),
                    user_id=self.user_id,
                    name=account_data["name"],
                    description=account_data["description"],
                    currency=account_data["currency"],
                    is_shared=account_data["is_shared"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(account)
                self.account_ids.append(account.id)
                print(f"  ✅ {account.name}")

            await session.commit()

        print(f"📚 创建了 {len(accounts_data)} 个账本")

    async def create_mock_assets(self):
        """创建示例资产"""
        print("\n💰 创建示例资产...")

        assets_data = [
            # 现金类
            {"name": "现金", "type": AssetTypeEnum.CASH, "balance": "2000.00"},
            {"name": "微信钱包", "type": AssetTypeEnum.CASH, "balance": "1500.50"},
            {"name": "支付宝余额", "type": AssetTypeEnum.CASH, "balance": "3200.80"},
            # 银行卡类
            {
                "name": "招商银行储蓄卡",
                "type": AssetTypeEnum.BANK_CARD,
                "balance": "25000.00",
            },
            {
                "name": "工商银行信用卡",
                "type": AssetTypeEnum.CREDIT_CARD,
                "balance": "-1200.00",
            },
            {
                "name": "建设银行储蓄卡",
                "type": AssetTypeEnum.BANK_CARD,
                "balance": "15800.75",
            },
            # 投资类
            {
                "name": "股票账户",
                "type": AssetTypeEnum.INVESTMENT,
                "balance": "50000.00",
            },
            {
                "name": "基金定投",
                "type": AssetTypeEnum.INVESTMENT,
                "balance": "32000.00",
            },
            {"name": "余额宝", "type": AssetTypeEnum.INVESTMENT, "balance": "8500.00"},
            # 其他
            {"name": "公积金账户", "type": AssetTypeEnum.OTHER, "balance": "45000.00"},
        ]

        async with db.get_session() as session:
            for asset_data in assets_data:
                asset = Asset(
                    id=uuid.uuid4(),
                    user_id=self.user_id,
                    name=asset_data["name"],
                    asset_type=asset_data["type"],
                    balance=Decimal(asset_data["balance"]),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(asset)
                self.asset_ids.append(asset.id)
                print(f"  ✅ {asset.name}: ¥{asset.balance}")

            await session.commit()

        print(f"💰 创建了 {len(assets_data)} 个资产")

    async def create_mock_categories(self):
        """创建示例分类"""
        print("\n🏷️  创建示例分类...")

        # 一级分类
        primary_categories = [
            {"name": "餐饮美食", "description": "餐厅用餐、外卖、零食等"},
            {"name": "交通出行", "description": "公交、地铁、打车、加油等"},
            {"name": "购物消费", "description": "服装、日用品、电子产品等"},
            {"name": "居住生活", "description": "房租、水电、物业费等"},
            {"name": "娱乐休闲", "description": "电影、旅游、运动等"},
            {"name": "医疗健康", "description": "看病、买药、体检等"},
            {"name": "学习教育", "description": "培训、书籍、课程等"},
            {"name": "工资收入", "description": "主要工作收入"},
            {"name": "投资收益", "description": "股票、基金、理财收益"},
            {"name": "其他收入", "description": "兼职、奖金等其他收入"},
        ]

        # 二级分类
        sub_categories = {
            "餐饮美食": ["正餐", "早餐", "下午茶", "夜宵", "零食饮料"],
            "交通出行": ["公共交通", "打车费用", "加油费", "停车费", "车辆保养"],
            "购物消费": ["服装鞋帽", "日用百货", "数码电器", "美妆护肤", "图书文具"],
            "居住生活": ["房租房贷", "水电煤气", "物业费", "家具家电", "房屋维修"],
            "娱乐休闲": ["电影演出", "旅游度假", "运动健身", "游戏娱乐", "聚会社交"],
        }

        async with db.get_session() as session:
            # 创建一级分类
            primary_category_map = {}
            for cat_data in primary_categories:
                category = Category(
                    id=uuid.uuid4(),
                    user_id=self.user_id,
                    name=cat_data["name"],
                    description=cat_data["description"],
                    is_system=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(category)
                self.category_ids.append(category.id)
                primary_category_map[cat_data["name"]] = category.id
                print(f"  ✅ {category.name}")

            await session.commit()

            # 创建二级分类
            for parent_name, sub_names in sub_categories.items():
                parent_id = primary_category_map.get(parent_name)
                if parent_id:
                    for sub_name in sub_names:
                        sub_category = Category(
                            id=uuid.uuid4(),
                            user_id=self.user_id,
                            name=sub_name,
                            description=f"{parent_name}下的{sub_name}分类",
                            parent_category_id=parent_id,
                            is_system=False,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )

                        session.add(sub_category)
                        self.category_ids.append(sub_category.id)
                        print(f"    ↳ {sub_name}")

            await session.commit()

        print(f"🏷️  创建了分类体系")

    async def create_mock_bills(self):
        """创建示例账单"""
        print("\n📝 创建示例账单...")

        # 确保有足够的数据
        if not self.account_ids or not self.asset_ids or not self.category_ids:
            print("❌ 缺少必要的关联数据，请先创建账本、资产和分类")
            return

        bills_data = []

        # 生成近30天的账单数据
        base_date = datetime.now() - timedelta(days=30)

        # 支出账单示例
        expense_examples = [
            {
                "amount": "25.80",
                "description": "麦当劳午餐",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "12.00",
                "description": "地铁通勤",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "138.50",
                "description": "超市购物",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "89.00",
                "description": "电影票",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "45.60",
                "description": "咖啡厅",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "230.00",
                "description": "加油费",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "68.88",
                "description": "外卖晚餐",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "156.00",
                "description": "话费充值",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "299.00",
                "description": "健身月卡",
                "type": TransactionTypeEnum.EXPENSE,
            },
            {
                "amount": "78.50",
                "description": "药店买药",
                "type": TransactionTypeEnum.EXPENSE,
            },
        ]

        # 收入账单示例
        income_examples = [
            {
                "amount": "8500.00",
                "description": "工资收入",
                "type": TransactionTypeEnum.INCOME,
            },
            {
                "amount": "200.00",
                "description": "兼职收入",
                "type": TransactionTypeEnum.INCOME,
            },
            {
                "amount": "150.50",
                "description": "基金分红",
                "type": TransactionTypeEnum.INCOME,
            },
            {
                "amount": "500.00",
                "description": "奖金",
                "type": TransactionTypeEnum.INCOME,
            },
        ]

        # 生成30天内的随机账单
        for i in range(50):  # 生成50条账单
            # 随机选择收入或支出
            if random.random() < 0.8:  # 80%概率是支出
                bill_data = random.choice(expense_examples)
            else:
                bill_data = random.choice(income_examples)

            # 随机日期
            random_days = random.randint(0, 30)
            bill_date = base_date + timedelta(days=random_days)

            bills_data.append(
                {
                    "account_id": random.choice(self.account_ids),
                    "asset_id": random.choice(self.asset_ids),
                    "category_id": random.choice(self.category_ids),
                    "amount": Decimal(bill_data["amount"]),
                    "transaction_type": bill_data["type"],
                    "description": bill_data["description"],
                    "transaction_date": bill_date,
                    "created_at": datetime.utcnow(),
                }
            )

        async with db.get_session() as session:
            for bill_data in bills_data:
                bill = Bill(
                    id=uuid.uuid4(),
                    user_id=self.user_id,
                    **bill_data,
                    updated_at=datetime.utcnow(),
                )

                session.add(bill)

                # 打印账单信息
                type_icon = (
                    "💰"
                    if bill.transaction_type == TransactionTypeEnum.INCOME
                    else "💸"
                )
                print(
                    f"  {type_icon} ¥{bill.amount} - {bill.description} ({bill.transaction_date.strftime('%m-%d')})"
                )

            await session.commit()

        print(f"📝 创建了 {len(bills_data)} 条账单")

    async def generate_summary(self):
        """生成数据汇总"""
        print("\n📊 数据汇总:")
        print("=" * 50)

        async with db.get_session() as session:
            # 用户信息
            user_stmt = select(User).where(User.id == self.user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one()

            print(f"👤 用户: {user.username} ({user.email})")
            print(f"🔑 密码: test123")
            print(f"🆔 用户ID: {user.id}")

            # 账本统计
            account_stmt = select(Account).where(Account.user_id == self.user_id)
            account_result = await session.execute(account_stmt)
            accounts = account_result.scalars().all()
            print(f"📚 账本数量: {len(accounts)}")

            # 资产统计
            asset_stmt = select(Asset).where(Asset.user_id == self.user_id)
            asset_result = await session.execute(asset_stmt)
            assets = asset_result.scalars().all()
            total_balance = sum(asset.balance for asset in assets)
            print(f"💰 资产数量: {len(assets)}")
            print(f"💎 总资产: ¥{total_balance}")

            # 分类统计
            category_stmt = select(Category).where(Category.user_id == self.user_id)
            category_result = await session.execute(category_stmt)
            categories = category_result.scalars().all()
            print(f"🏷️  分类数量: {len(categories)}")

            # 账单统计
            bill_stmt = select(Bill).where(Bill.user_id == self.user_id)
            bill_result = await session.execute(bill_stmt)
            bills = bill_result.scalars().all()

            income_bills = [
                b for b in bills if b.transaction_type == TransactionTypeEnum.INCOME
            ]
            expense_bills = [
                b for b in bills if b.transaction_type == TransactionTypeEnum.EXPENSE
            ]

            total_income = sum(bill.amount for bill in income_bills)
            total_expense = sum(bill.amount for bill in expense_bills)

            print(f"📝 账单数量: {len(bills)}")
            print(f"💰 总收入: ¥{total_income}")
            print(f"💸 总支出: ¥{total_expense}")
            print(f"📈 净收益: ¥{total_income - total_expense}")

        print("=" * 50)
        print("✅ Mock数据生成完成！")
        print("\n🚀 可以开始测试API功能了:")
        print("- 登录: POST /api/v1/auth/login")
        print("- 账本: GET /api/v1/accounts")
        print("- 资产: GET /api/v1/assets")
        print("- 分类: GET /api/v1/categories")
        print("- 账单: GET /api/v1/bills")

    async def run(self):
        """运行完整的Mock数据生成流程"""
        print("🧪 开始生成Mock数据...")
        print("=" * 50)

        try:
            # 初始化数据库
            await init_database()

            # 按依赖关系顺序创建数据
            await self.create_test_user()
            await self.create_mock_accounts()
            await self.create_mock_assets()
            await self.create_mock_categories()
            await self.create_mock_bills()

            # 生成汇总报告
            await self.generate_summary()

        except Exception as e:
            print(f"❌ 生成Mock数据失败: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await db.disconnect()


async def main():
    """主函数"""
    generator = MockDataGenerator()
    await generator.run()


if __name__ == "__main__":
    asyncio.run(main())
