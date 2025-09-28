#!/usr/bin/env python3
"""
完整Mock数据生成 - 修复版本
"""

import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def main():
    # 生成随机用户
    random_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
    user_data = {
        "username": f"testuser_{random_suffix}",
        "email": f"test_{random_suffix}@example.com",
        "password": "test123",
    }

    print(f"🧪 创建完整Mock数据")
    print(f"👤 用户: {user_data['username']} / {user_data['password']}")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 1. 注册用户
        print("📝 注册用户...")
        async with session.post(f"{API_BASE}/auth/register", json=user_data) as resp:
            data = await resp.json()
            if resp.status in [200, 201]:
                print(f"✅ 注册成功: {data['message']}")
            else:
                print(f"❌ 注册失败: {data}")
                return

        # 2. 登录
        print("🔑 用户登录...")
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        async with session.post(f"{API_BASE}/auth/login", json=login_data) as resp:
            data = await resp.json()
            if resp.status == 200:
                token = data["data"]["access_token"]
                print(f"✅ 登录成功")
            else:
                print(f"❌ 登录失败: {data}")
                return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 3. 创建账本
        print("\n📚 创建账本...")
        accounts = []
        accounts_data = [
            {"name": "个人账本", "description": "个人日常开销", "currency": "CNY"},
            {
                "name": "家庭账本",
                "description": "家庭共同开销",
                "currency": "CNY",
                "is_shared": True,
            },
        ]

        for acc_data in accounts_data:
            async with session.post(
                f"{API_BASE}/accounts", json=acc_data, headers=headers
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    account = data["data"]
                    accounts.append(account)
                    print(f"✅ {account['name']} (ID: {account['id'][:8]}...)")

        # 4. 创建资产
        print("\n💰 创建资产...")
        assets = []
        assets_data = [
            {"name": "现金", "asset_type": "CASH", "balance": "2000.00"},
            {"name": "招商银行", "asset_type": "BANK_CARD", "balance": "15000.00"},
            {"name": "支付宝", "asset_type": "CASH", "balance": "800.50"},
            {"name": "股票账户", "asset_type": "INVESTMENT", "balance": "25000.00"},
        ]

        for asset_data in assets_data:
            async with session.post(
                f"{API_BASE}/assets", json=asset_data, headers=headers
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    asset = data["data"]
                    assets.append(asset)
                    print(f"✅ {asset['name']}: ¥{asset['balance']}")

        # 5. 创建分类
        print("\n🏷️  创建分类...")
        categories = []

        # 主分类
        main_cats = [
            {"name": "餐饮美食", "description": "用餐相关支出"},
            {"name": "交通出行", "description": "交通费用"},
            {"name": "购物消费", "description": "购物支出"},
            {"name": "工资收入", "description": "工作收入"},
            {"name": "投资收益", "description": "投资获利"},
        ]

        for cat_data in main_cats:
            async with session.post(
                f"{API_BASE}/categories", json=cat_data, headers=headers
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    category = data["data"]
                    categories.append(category)
                    print(f"✅ {category['name']}")

        # 子分类
        if categories:
            sub_cats = [
                {
                    "name": "正餐",
                    "description": "正餐消费",
                    "parent_category_id": categories[0]["id"],
                },
                {
                    "name": "零食",
                    "description": "零食饮料",
                    "parent_category_id": categories[0]["id"],
                },
                {
                    "name": "公交地铁",
                    "description": "公共交通",
                    "parent_category_id": categories[1]["id"],
                },
                {
                    "name": "打车",
                    "description": "打车费用",
                    "parent_category_id": categories[1]["id"],
                },
            ]

            for cat_data in sub_cats:
                async with session.post(
                    f"{API_BASE}/categories", json=cat_data, headers=headers
                ) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        category = data["data"]
                        categories.append(category)
                        print(f"  ↳ {category['name']}")

        # 6. 创建账单
        print("\n📝 创建账单...")
        bills_count = 0

        if accounts and assets and categories:
            # 示例账单数据
            bills_examples = [
                # 支出
                {"amount": "35.80", "desc": "午餐", "type": "EXPENSE", "cat_idx": 0},
                {"amount": "12.00", "desc": "地铁", "type": "EXPENSE", "cat_idx": 1},
                {
                    "amount": "156.70",
                    "desc": "超市购物",
                    "type": "EXPENSE",
                    "cat_idx": 2,
                },
                {"amount": "68.50", "desc": "咖啡", "type": "EXPENSE", "cat_idx": 0},
                {"amount": "15.00", "desc": "公交", "type": "EXPENSE", "cat_idx": 1},
                # 收入
                {"amount": "8500.00", "desc": "工资", "type": "INCOME", "cat_idx": 3},
                {
                    "amount": "280.50",
                    "desc": "基金收益",
                    "type": "INCOME",
                    "cat_idx": 4,
                },
                {"amount": "150.00", "desc": "兼职", "type": "INCOME", "cat_idx": 3},
            ]

            base_date = datetime.now() - timedelta(days=15)

            for i, bill_example in enumerate(bills_examples):
                bill_date = base_date + timedelta(days=random.randint(0, 15))

                bill_data = {
                    "account_id": random.choice(accounts)["id"],
                    "asset_id": random.choice(assets)["id"],
                    "category_id": categories[bill_example["cat_idx"]]["id"],
                    "amount": bill_example["amount"],
                    "transaction_type": bill_example["type"],
                    "description": bill_example["desc"],
                    "transaction_date": bill_date.isoformat(),
                }

                async with session.post(
                    f"{API_BASE}/bills", json=bill_data, headers=headers
                ) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        bill = data["data"]
                        bills_count += 1

                        type_icon = (
                            "💰" if bill["transaction_type"] == "INCOME" else "💸"
                        )
                        print(
                            f"✅ {type_icon} ¥{bill['amount']} - {bill['description']}"
                        )

        # 7. 最终汇总
        print("\n📊 Mock数据创建完成!")
        print("=" * 60)
        print(f"👤 用户名: {user_data['username']}")
        print(f"📧 邮箱: {user_data['email']}")
        print(f"🔑 密码: {user_data['password']}")
        print(f"🎫 Token: {token[:50]}...")
        print(f"📚 账本: {len(accounts)} 个")
        print(f"💰 资产: {len(assets)} 个")
        print(f"🏷️  分类: {len(categories)} 个")
        print(f"📝 账单: {bills_count} 条")
        print("=" * 60)
        print(f"🌐 API文档: {BASE_URL}/docs")
        print("✅ 现在可以用这个用户测试所有API功能了！")


if __name__ == "__main__":
    asyncio.run(main())
