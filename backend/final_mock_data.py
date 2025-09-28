#!/usr/bin/env python3
"""
最终Mock数据生成脚本 - 修正版本
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


async def create_final_mock_data():
    print("🧪 创建最终Mock数据")
    print("=" * 60)

    # 使用已有用户
    user_data = {"email": "test_uswxfh@example.com", "password": "test123"}

    async with aiohttp.ClientSession() as session:
        # 登录
        print("🔑 登录用户...")
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

        # 创建资产 - 使用正确的字段名
        print("\n💰 创建资产...")
        assets = []
        assets_data = [
            {"name": "现金", "type": "CASH", "balance": "2000.00"},
            {"name": "招商银行卡", "type": "BANK_CARD", "balance": "15000.00"},
            {"name": "支付宝", "type": "CASH", "balance": "800.50"},
            {"name": "微信钱包", "type": "CASH", "balance": "300.00"},
            {"name": "股票账户", "type": "INVESTMENT", "balance": "25000.00"},
            {"name": "信用卡", "type": "CREDIT_CARD", "balance": "-1200.00"},
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

        # 创建分类 - 使用正确的字段名和类型
        print("\n🏷️ 创建分类...")
        categories = []

        # 支出分类
        expense_categories = [
            {"name": "餐饮美食", "type": "EXPENSE"},
            {"name": "交通出行", "type": "EXPENSE"},
            {"name": "购物消费", "type": "EXPENSE"},
            {"name": "居住生活", "type": "EXPENSE"},
            {"name": "娱乐休闲", "type": "EXPENSE"},
        ]

        for cat_data in expense_categories:
            async with session.post(
                f"{BASE_URL}/api/v1/categories", json=cat_data, headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    category = data["data"]
                    categories.append(category)
                    print(f"✅ {category['name']} (支出)")
                else:
                    error = await resp.json()
                    print(f"❌ 创建分类失败: {error}")

        # 收入分类
        income_categories = [
            {"name": "工资收入", "type": "INCOME"},
            {"name": "投资收益", "type": "INCOME"},
            {"name": "其他收入", "type": "INCOME"},
        ]

        for cat_data in income_categories:
            async with session.post(
                f"{BASE_URL}/api/v1/categories", json=cat_data, headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    category = data["data"]
                    categories.append(category)
                    print(f"✅ {category['name']} (收入)")
                else:
                    error = await resp.json()
                    print(f"❌ 创建分类失败: {error}")

        # 获取账本
        async with session.get(f"{BASE_URL}/api/v1/accounts", headers=headers) as resp:
            data = await resp.json()
            accounts = data["data"]["items"]

        # 创建账单
        print("\n📝 创建账单...")
        bills_count = 0

        if accounts and assets and categories:
            # 找到收入和支出分类
            expense_cats = [cat for cat in categories if cat.get("type") == "EXPENSE"]
            income_cats = [cat for cat in categories if cat.get("type") == "INCOME"]

            # 账单模板
            bill_templates = [
                # 支出账单
                {"amount": "35.80", "desc": "麦当劳午餐", "type": "EXPENSE"},
                {"amount": "25.50", "desc": "星巴克咖啡", "type": "EXPENSE"},
                {"amount": "12.00", "desc": "地铁费", "type": "EXPENSE"},
                {"amount": "25.00", "desc": "打车费", "type": "EXPENSE"},
                {"amount": "158.90", "desc": "超市购物", "type": "EXPENSE"},
                {"amount": "89.00", "desc": "电影票", "type": "EXPENSE"},
                {"amount": "299.00", "desc": "运动鞋", "type": "EXPENSE"},
                {"amount": "68.50", "desc": "外卖晚餐", "type": "EXPENSE"},
                {"amount": "15.80", "desc": "零食", "type": "EXPENSE"},
                {"amount": "45.00", "desc": "公交月卡", "type": "EXPENSE"},
                {"amount": "1200.00", "desc": "房租", "type": "EXPENSE"},
                {"amount": "350.00", "desc": "水电费", "type": "EXPENSE"},
                # 收入账单
                {"amount": "8500.00", "desc": "工资收入", "type": "INCOME"},
                {"amount": "280.50", "desc": "基金分红", "type": "INCOME"},
                {"amount": "150.00", "desc": "兼职收入", "type": "INCOME"},
                {"amount": "500.00", "desc": "年终奖金", "type": "INCOME"},
                {"amount": "120.30", "desc": "股票收益", "type": "INCOME"},
            ]

            # 生成过去30天的账单
            base_date = datetime.now() - timedelta(days=30)

            for template in bill_templates:
                # 随机日期
                random_days = random.randint(0, 30)
                bill_date = base_date + timedelta(days=random_days)

                # 根据账单类型选择分类
                if template["type"] == "EXPENSE" and expense_cats:
                    category_id = random.choice(expense_cats)["id"]
                elif template["type"] == "INCOME" and income_cats:
                    category_id = random.choice(income_cats)["id"]
                else:
                    continue  # 跳过没有对应分类的账单

                bill_data = {
                    "account_id": random.choice(accounts)["id"],
                    "asset_id": random.choice(assets)["id"],
                    "category_id": category_id,
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
                            f"✅ {type_icon} ¥{bill['amount']} - {bill['description']}"
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
        print("✅ 完整的测试数据已创建！")


if __name__ == "__main__":
    asyncio.run(create_final_mock_data())
