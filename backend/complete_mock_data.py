#!/usr/bin/env python3
"""
使用已有用户完善Mock数据
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


async def complete_mock_data():
    print("🧪 完善Mock数据")
    print("=" * 60)

    # 使用已有用户
    user_data = {"email": "test_uswxfh@example.com", "password": "test123"}

    async with aiohttp.ClientSession() as session:
        # 登录
        print("🔑 登录已有用户...")
        async with session.post(
            f"{BASE_URL}/api/v1/auth/login", json=user_data
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data["data"]["access_token"]
                print(f"✅ 登录成功")
            else:
                print(f"❌ 登录失败")
                return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 获取已有账本
        async with session.get(f"{BASE_URL}/api/v1/accounts", headers=headers) as resp:
            data = await resp.json()
            existing_accounts = data["data"]["items"]
            print(f"📚 已有账本: {len(existing_accounts)} 个")

        # 创建资产
        print("\n💰 创建资产...")
        assets = []
        assets_data = [
            {"name": "现金", "asset_type": "CASH", "balance": "2000.00"},
            {"name": "招商银行卡", "asset_type": "BANK_CARD", "balance": "15000.00"},
            {"name": "支付宝", "asset_type": "CASH", "balance": "800.50"},
            {"name": "微信钱包", "asset_type": "CASH", "balance": "300.00"},
            {"name": "股票账户", "asset_type": "INVESTMENT", "balance": "25000.00"},
            {"name": "信用卡", "asset_type": "CREDIT_CARD", "balance": "-1200.00"},
        ]

        for asset_data in assets_data:
            async with session.post(
                f"{BASE_URL}/api/v1/assets", json=asset_data, headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    asset = data["data"]
                    assets.append(asset)
                    print(f"✅ {asset['name']}: ¥{asset['balance']}")
                else:
                    error = await resp.json()
                    print(f"❌ 创建资产失败: {error}")

        # 创建分类
        print("\n🏷️ 创建分类...")
        categories = []

        # 主分类
        main_categories = [
            {"name": "餐饮美食", "description": "餐厅用餐、外卖、零食等"},
            {"name": "交通出行", "description": "公交、地铁、打车、加油等"},
            {"name": "购物消费", "description": "服装、日用品、电子产品等"},
            {"name": "居住生活", "description": "房租、水电、物业费等"},
            {"name": "娱乐休闲", "description": "电影、旅游、运动等"},
            {"name": "工资收入", "description": "主要工作收入"},
            {"name": "投资收益", "description": "股票、基金、理财收益"},
            {"name": "其他收入", "description": "兼职、奖金等其他收入"},
        ]

        for cat_data in main_categories:
            async with session.post(
                f"{BASE_URL}/api/v1/categories", json=cat_data, headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    category = data["data"]
                    categories.append(category)
                    print(f"✅ {category['name']}")
                else:
                    error = await resp.json()
                    print(f"❌ 创建分类失败: {error}")

        # 创建子分类
        sub_categories_data = [
            {
                "name": "正餐",
                "description": "正餐消费",
                "parent_category_id": categories[0]["id"],
            },
            {
                "name": "零食饮料",
                "description": "零食和饮料",
                "parent_category_id": categories[0]["id"],
            },
            {
                "name": "公共交通",
                "description": "地铁公交",
                "parent_category_id": categories[1]["id"],
            },
            {
                "name": "打车费",
                "description": "出租车网约车",
                "parent_category_id": categories[1]["id"],
            },
            {
                "name": "服装鞋帽",
                "description": "服装类购物",
                "parent_category_id": categories[2]["id"],
            },
            {
                "name": "数码电器",
                "description": "电子产品",
                "parent_category_id": categories[2]["id"],
            },
        ]

        for cat_data in sub_categories_data:
            async with session.post(
                f"{BASE_URL}/api/v1/categories", json=cat_data, headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    category = data["data"]
                    categories.append(category)
                    print(f"  ↳ {category['name']}")

        # 创建账单
        print("\n📝 创建账单...")
        bills_count = 0

        if existing_accounts and assets and categories:
            # 账单模板
            bill_templates = [
                # 支出
                {"amount": "35.80", "desc": "麦当劳午餐", "type": "EXPENSE", "cat": 0},
                {"amount": "25.50", "desc": "星巴克咖啡", "type": "EXPENSE", "cat": 0},
                {"amount": "12.00", "desc": "地铁费", "type": "EXPENSE", "cat": 1},
                {"amount": "25.00", "desc": "打车费", "type": "EXPENSE", "cat": 1},
                {"amount": "158.90", "desc": "超市购物", "type": "EXPENSE", "cat": 2},
                {"amount": "89.00", "desc": "电影票", "type": "EXPENSE", "cat": 4},
                {"amount": "299.00", "desc": "运动鞋", "type": "EXPENSE", "cat": 2},
                {"amount": "68.50", "desc": "外卖晚餐", "type": "EXPENSE", "cat": 0},
                {"amount": "15.80", "desc": "零食", "type": "EXPENSE", "cat": 0},
                {"amount": "45.00", "desc": "公交月卡", "type": "EXPENSE", "cat": 1},
                # 收入
                {"amount": "8500.00", "desc": "工资收入", "type": "INCOME", "cat": 5},
                {"amount": "280.50", "desc": "基金分红", "type": "INCOME", "cat": 6},
                {"amount": "150.00", "desc": "兼职收入", "type": "INCOME", "cat": 7},
                {"amount": "500.00", "desc": "年终奖金", "type": "INCOME", "cat": 5},
                {"amount": "120.30", "desc": "股票收益", "type": "INCOME", "cat": 6},
            ]

            # 生成过去30天的账单
            base_date = datetime.now() - timedelta(days=30)

            for i, template in enumerate(bill_templates):
                # 随机日期
                random_days = random.randint(0, 30)
                bill_date = base_date + timedelta(days=random_days)

                bill_data = {
                    "account_id": random.choice(existing_accounts)["id"],
                    "asset_id": random.choice(assets)["id"],
                    "category_id": categories[template["cat"]]["id"],
                    "amount": template["amount"],
                    "transaction_type": template["type"],
                    "description": template["desc"],
                    "transaction_date": bill_date.isoformat(),
                }

                async with session.post(
                    f"{BASE_URL}/api/v1/bills", json=bill_data, headers=headers
                ) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        bill = data["data"]
                        bills_count += 1

                        type_icon = (
                            "💰" if bill["transaction_type"] == "INCOME" else "💸"
                        )
                        print(
                            f"✅ {type_icon} ¥{bill['amount']} - {bill['description']} ({bill_date.strftime('%m-%d')})"
                        )
                    else:
                        error = await resp.json()
                        print(f"❌ 创建账单失败: {error}")

        # 生成最终报告
        print("\n📊 Mock数据创建完成!")
        print("=" * 60)

        # 获取汇总数据
        async with session.get(f"{BASE_URL}/api/v1/accounts", headers=headers) as resp:
            data = await resp.json()
            total_accounts = len(data["data"]["items"])

        async with session.get(f"{BASE_URL}/api/v1/assets", headers=headers) as resp:
            data = await resp.json()
            assets_list = data["data"]["items"]
            total_assets = len(assets_list)
            total_balance = sum(float(asset["balance"]) for asset in assets_list)

        async with session.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        ) as resp:
            data = await resp.json()
            total_categories = len(data["data"])

        async with session.get(f"{BASE_URL}/api/v1/bills", headers=headers) as resp:
            data = await resp.json()
            bills_list = data["data"]["items"]
            total_bills = len(bills_list)

            income_bills = [b for b in bills_list if b["transaction_type"] == "INCOME"]
            expense_bills = [
                b for b in bills_list if b["transaction_type"] == "EXPENSE"
            ]
            total_income = sum(float(b["amount"]) for b in income_bills)
            total_expense = sum(float(b["amount"]) for b in expense_bills)

        print(f"👤 用户: testuser_uswxfh")
        print(f"📧 邮箱: test_uswxfh@example.com")
        print(f"🔑 密码: test123")
        print(f"📚 账本总数: {total_accounts} 个")
        print(f"💰 资产总数: {total_assets} 个")
        print(f"💎 总资产: ¥{total_balance:.2f}")
        print(f"🏷️ 分类总数: {total_categories} 个")
        print(f"📝 账单总数: {total_bills} 条")
        print(f"💰 总收入: ¥{total_income:.2f}")
        print(f"💸 总支出: ¥{total_expense:.2f}")
        print(f"📈 净收益: ¥{total_income - total_expense:.2f}")
        print("=" * 60)
        print(f"🌐 API文档: {BASE_URL}/docs")
        print("✅ 现在可以用完整数据测试所有功能了！")


if __name__ == "__main__":
    asyncio.run(complete_mock_data())
