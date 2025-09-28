#!/usr/bin/env python3
"""
通过真实API接口创建Mock数据
使用HTTP请求调用实际的API端点来创建测试数据
"""

import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

BASE_URL = f"http://localhost:{settings.SERVER_PORT}"
API_BASE = f"{BASE_URL}/api/v1"


class ApiMockDataGenerator:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.user_data = {
            "username": "test",
            "email": "test@example.com",
            "password": "test123",
        }
        self.created_accounts = []
        self.created_assets = []
        self.created_categories = []

    async def setup(self):
        """初始化HTTP会话"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 初始化API客户端")
        print(f"📍 API地址: {API_BASE}")

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()

    async def register_and_login(self):
        """注册并登录用户"""
        print("\n👤 创建并登录测试用户...")

        # 尝试注册用户
        try:
            async with self.session.post(
                f"{API_BASE}/auth/register",
                json=self.user_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ 用户注册成功: {self.user_data['username']}")
                elif response.status == 400:
                    print(f"ℹ️  用户可能已存在，继续登录...")
                else:
                    error_data = await response.json()
                    print(f"❌ 注册失败: {error_data}")
        except Exception as e:
            print(f"ℹ️  注册请求异常: {e}，继续尝试登录...")

        # 登录用户
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"],
        }

        async with self.session.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.access_token = data["data"]["access_token"]
                print(f"✅ 登录成功，获取到访问令牌")
                return True
            else:
                error_data = await response.json()
                print(f"❌ 登录失败: {error_data}")
                return False

    def get_auth_headers(self):
        """获取认证头"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def create_mock_accounts(self):
        """通过API创建示例账本"""
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

        for account_data in accounts_data:
            async with self.session.post(
                f"{API_BASE}/accounts",
                json=account_data,
                headers=self.get_auth_headers(),
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    account = data["data"]
                    self.created_accounts.append(account)
                    print(f"  ✅ {account['name']} (ID: {account['id']})")
                else:
                    error_data = await response.json()
                    print(f"  ❌ 创建账本失败: {error_data}")

        print(f"📚 成功创建了 {len(self.created_accounts)} 个账本")

    async def create_mock_assets(self):
        """通过API创建示例资产"""
        print("\n💰 创建示例资产...")

        assets_data = [
            # 现金类
            {"name": "现金", "asset_type": "CASH", "balance": "2000.00"},
            {"name": "微信钱包", "asset_type": "CASH", "balance": "1500.50"},
            {"name": "支付宝余额", "asset_type": "CASH", "balance": "3200.80"},
            # 银行卡类
            {
                "name": "招商银行储蓄卡",
                "asset_type": "BANK_CARD",
                "balance": "25000.00",
            },
            {
                "name": "工商银行信用卡",
                "asset_type": "CREDIT_CARD",
                "balance": "-1200.00",
            },
            {
                "name": "建设银行储蓄卡",
                "asset_type": "BANK_CARD",
                "balance": "15800.75",
            },
            # 投资类
            {"name": "股票账户", "asset_type": "INVESTMENT", "balance": "50000.00"},
            {"name": "基金定投", "asset_type": "INVESTMENT", "balance": "32000.00"},
            {"name": "余额宝", "asset_type": "INVESTMENT", "balance": "8500.00"},
            # 其他
            {"name": "公积金账户", "asset_type": "OTHER", "balance": "45000.00"},
        ]

        for asset_data in assets_data:
            async with self.session.post(
                f"{API_BASE}/assets", json=asset_data, headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    asset = data["data"]
                    self.created_assets.append(asset)
                    print(f"  ✅ {asset['name']}: ¥{asset['balance']}")
                else:
                    error_data = await response.json()
                    print(f"  ❌ 创建资产失败: {error_data}")

        print(f"💰 成功创建了 {len(self.created_assets)} 个资产")

    async def create_mock_categories(self):
        """通过API创建示例分类"""
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

        # 创建一级分类
        primary_category_map = {}
        for cat_data in primary_categories:
            async with self.session.post(
                f"{API_BASE}/categories", json=cat_data, headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    category = data["data"]
                    self.created_categories.append(category)
                    primary_category_map[category["name"]] = category["id"]
                    print(f"  ✅ {category['name']}")
                else:
                    error_data = await response.json()
                    print(f"  ❌ 创建分类失败: {error_data}")

        # 二级分类
        sub_categories = {
            "餐饮美食": ["正餐", "早餐", "下午茶", "夜宵", "零食饮料"],
            "交通出行": ["公共交通", "打车费用", "加油费", "停车费", "车辆保养"],
            "购物消费": ["服装鞋帽", "日用百货", "数码电器", "美妆护肤", "图书文具"],
            "居住生活": ["房租房贷", "水电煤气", "物业费", "家具家电", "房屋维修"],
            "娱乐休闲": ["电影演出", "旅游度假", "运动健身", "游戏娱乐", "聚会社交"],
        }

        # 创建二级分类
        for parent_name, sub_names in sub_categories.items():
            parent_id = primary_category_map.get(parent_name)
            if parent_id:
                for sub_name in sub_names:
                    sub_category_data = {
                        "name": sub_name,
                        "description": f"{parent_name}下的{sub_name}分类",
                        "parent_category_id": parent_id,
                    }

                    async with self.session.post(
                        f"{API_BASE}/categories",
                        json=sub_category_data,
                        headers=self.get_auth_headers(),
                    ) as response:
                        if response.status == 201:
                            data = await response.json()
                            category = data["data"]
                            self.created_categories.append(category)
                            print(f"    ↳ {category['name']}")
                        else:
                            error_data = await response.json()
                            print(f"    ❌ 创建子分类失败: {error_data}")

        print(f"🏷️  成功创建了 {len(self.created_categories)} 个分类")

    async def create_mock_bills(self):
        """通过API创建示例账单"""
        print("\n📝 创建示例账单...")

        if (
            not self.created_accounts
            or not self.created_assets
            or not self.created_categories
        ):
            print("❌ 缺少必要的关联数据，请先创建账本、资产和分类")
            return

        # 支出账单示例
        expense_examples = [
            {
                "amount": "25.80",
                "description": "麦当劳午餐",
                "transaction_type": "EXPENSE",
            },
            {
                "amount": "12.00",
                "description": "地铁通勤",
                "transaction_type": "EXPENSE",
            },
            {
                "amount": "138.50",
                "description": "超市购物",
                "transaction_type": "EXPENSE",
            },
            {"amount": "89.00", "description": "电影票", "transaction_type": "EXPENSE"},
            {"amount": "45.60", "description": "咖啡厅", "transaction_type": "EXPENSE"},
            {
                "amount": "230.00",
                "description": "加油费",
                "transaction_type": "EXPENSE",
            },
            {
                "amount": "68.88",
                "description": "外卖晚餐",
                "transaction_type": "EXPENSE",
            },
            {
                "amount": "156.00",
                "description": "话费充值",
                "transaction_type": "EXPENSE",
            },
            {
                "amount": "299.00",
                "description": "健身月卡",
                "transaction_type": "EXPENSE",
            },
            {
                "amount": "78.50",
                "description": "药店买药",
                "transaction_type": "EXPENSE",
            },
        ]

        # 收入账单示例
        income_examples = [
            {
                "amount": "8500.00",
                "description": "工资收入",
                "transaction_type": "INCOME",
            },
            {
                "amount": "200.00",
                "description": "兼职收入",
                "transaction_type": "INCOME",
            },
            {
                "amount": "150.50",
                "description": "基金分红",
                "transaction_type": "INCOME",
            },
            {"amount": "500.00", "description": "奖金", "transaction_type": "INCOME"},
        ]

        # 生成近30天的账单数据
        base_date = datetime.now() - timedelta(days=30)
        created_bills = 0

        for i in range(50):  # 生成50条账单
            # 随机选择收入或支出
            if random.random() < 0.8:  # 80%概率是支出
                bill_template = random.choice(expense_examples)
            else:
                bill_template = random.choice(income_examples)

            # 随机日期
            random_days = random.randint(0, 30)
            bill_date = base_date + timedelta(days=random_days)

            bill_data = {
                "account_id": random.choice(self.created_accounts)["id"],
                "asset_id": random.choice(self.created_assets)["id"],
                "category_id": random.choice(self.created_categories)["id"],
                "amount": bill_template["amount"],
                "transaction_type": bill_template["transaction_type"],
                "description": bill_template["description"],
                "transaction_date": bill_date.isoformat(),
            }

            async with self.session.post(
                f"{API_BASE}/bills", json=bill_data, headers=self.get_auth_headers()
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    bill = data["data"]
                    created_bills += 1

                    # 打印账单信息
                    type_icon = "💰" if bill["transaction_type"] == "INCOME" else "💸"
                    print(
                        f"  {type_icon} ¥{bill['amount']} - {bill['description']} ({bill_date.strftime('%m-%d')})"
                    )
                else:
                    error_data = await response.json()
                    print(f"  ❌ 创建账单失败: {error_data}")

        print(f"📝 成功创建了 {created_bills} 条账单")

    async def generate_summary(self):
        """生成数据汇总报告"""
        print("\n📊 数据汇总:")
        print("=" * 50)

        # 获取用户信息
        async with self.session.get(
            f"{API_BASE}/auth/me", headers=self.get_auth_headers()
        ) as response:
            if response.status == 200:
                data = await response.json()
                user = data["data"]
                print(f"👤 用户: {user['username']} ({user['email']})")
                print(f"🔑 密码: test123")
                print(f"🆔 用户ID: {user['id']}")

        # 获取账本统计
        async with self.session.get(
            f"{API_BASE}/accounts", headers=self.get_auth_headers()
        ) as response:
            if response.status == 200:
                data = await response.json()
                accounts = (
                    data["data"]["items"] if "items" in data["data"] else data["data"]
                )
                print(f"📚 账本数量: {len(accounts)}")

        # 获取资产统计
        async with self.session.get(
            f"{API_BASE}/assets", headers=self.get_auth_headers()
        ) as response:
            if response.status == 200:
                data = await response.json()
                assets = (
                    data["data"]["items"] if "items" in data["data"] else data["data"]
                )
                total_balance = sum(float(asset["balance"]) for asset in assets)
                print(f"💰 资产数量: {len(assets)}")
                print(f"💎 总资产: ¥{total_balance:.2f}")

        # 获取分类统计
        async with self.session.get(
            f"{API_BASE}/categories", headers=self.get_auth_headers()
        ) as response:
            if response.status == 200:
                data = await response.json()
                categories = (
                    data["data"]["items"] if "items" in data["data"] else data["data"]
                )
                print(f"🏷️  分类数量: {len(categories)}")

        # 获取账单统计
        async with self.session.get(
            f"{API_BASE}/bills", headers=self.get_auth_headers()
        ) as response:
            if response.status == 200:
                data = await response.json()
                bills = (
                    data["data"]["items"] if "items" in data["data"] else data["data"]
                )

                income_bills = [b for b in bills if b["transaction_type"] == "INCOME"]
                expense_bills = [b for b in bills if b["transaction_type"] == "EXPENSE"]

                total_income = sum(float(bill["amount"]) for bill in income_bills)
                total_expense = sum(float(bill["amount"]) for bill in expense_bills)

                print(f"📝 账单数量: {len(bills)}")
                print(f"💰 总收入: ¥{total_income:.2f}")
                print(f"💸 总支出: ¥{total_expense:.2f}")
                print(f"📈 净收益: ¥{total_income - total_expense:.2f}")

        print("=" * 50)
        print("✅ Mock数据生成完成！")
        print("\n🚀 可以开始测试API功能了:")
        print(f"- API文档: {BASE_URL}/docs")
        print(f"- 登录令牌: {self.access_token[:50]}...")
        print("- 账本: GET /api/v1/accounts")
        print("- 资产: GET /api/v1/assets")
        print("- 分类: GET /api/v1/categories")
        print("- 账单: GET /api/v1/bills")

    async def run(self):
        """运行完整的Mock数据生成流程"""
        print("🧪 开始通过API生成Mock数据...")
        print("=" * 50)

        try:
            await self.setup()

            # 用户认证
            if not await self.register_and_login():
                print("❌ 无法获取访问令牌，停止执行")
                return

            # 按依赖关系顺序创建数据
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
            await self.cleanup()


async def main():
    """主函数"""
    generator = ApiMockDataGenerator()
    await generator.run()


if __name__ == "__main__":
    asyncio.run(main())
