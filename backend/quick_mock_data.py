#!/usr/bin/env python3
"""
快速Mock数据生成 - 使用新用户避免冲突
"""

import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def create_mock_data():
    """创建完整的mock数据"""

    # 生成随机用户
    random_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
    user_data = {
        "username": f"testuser_{random_suffix}",
        "email": f"test_{random_suffix}@example.com",
        "password": "test123",
    }

    print(f"🧪 创建Mock数据")
    print(f"👤 用户: {user_data['username']} / {user_data['password']}")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # 1. 注册用户
        print("📝 注册用户...")
        async with session.post(
            f"{API_BASE}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 201:
                data = await response.json()
                print(f"✅ 注册成功")
            else:
                error = await response.json()
                print(f"❌ 注册失败: {error}")
                return

        # 2. 登录获取token
        print("🔑 用户登录...")
        login_data = {"email": user_data["email"], "password": user_data["password"]}

        async with session.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 200:
                data = await response.json()
                access_token = data["data"]["access_token"]
                print(f"✅ 登录成功")
            else:
                error = await response.json()
                print(f"❌ 登录失败: {error}")
                return

        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # 3. 创建账本
        print("\n📚 创建账本...")
        accounts = []
        account_data = {
            "name": "测试账本",
            "description": "用于测试的账本",
            "currency": "CNY",
            "is_shared": False,
        }

        async with session.post(
            f"{API_BASE}/accounts", json=account_data, headers=auth_headers
        ) as response:
            if response.status == 201:
                data = await response.json()
                account = data["data"]
                accounts.append(account)
                print(f"✅ 账本: {account['name']} (ID: {account['id'][:8]}...)")
            else:
                error = await response.json()
                print(f"❌ 创建账本失败: {error}")

        # 4. 创建资产
        print("\n💰 创建资产...")
        assets = []
        assets_data = [
            {"name": "现金", "asset_type": "CASH", "balance": "1000.00"},
            {"name": "银行卡", "asset_type": "BANK_CARD", "balance": "5000.00"},
        ]

        for asset_data in assets_data:
            async with session.post(
                f"{API_BASE}/assets", json=asset_data, headers=auth_headers
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    asset = data["data"]
                    assets.append(asset)
                    print(f"✅ 资产: {asset['name']} ¥{asset['balance']}")
                else:
                    error = await response.json()
                    print(f"❌ 创建资产失败: {error}")

        # 5. 创建分类
        print("\n🏷️  创建分类...")
        categories = []
        categories_data = [
            {"name": "餐饮", "description": "用餐支出"},
            {"name": "交通", "description": "交通费用"},
            {"name": "收入", "description": "各种收入"},
        ]

        for cat_data in categories_data:
            async with session.post(
                f"{API_BASE}/categories", json=cat_data, headers=auth_headers
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    category = data["data"]
                    categories.append(category)
                    print(f"✅ 分类: {category['name']}")
                else:
                    error = await response.json()
                    print(f"❌ 创建分类失败: {error}")

        # 6. 创建账单
        print("\n📝 创建账单...")
        if accounts and assets and categories:
            bills_data = [
                {
                    "account_id": accounts[0]["id"],
                    "asset_id": assets[0]["id"],
                    "category_id": categories[0]["id"],
                    "amount": "25.50",
                    "transaction_type": "EXPENSE",
                    "description": "午餐",
                    "transaction_date": datetime.now().isoformat(),
                },
                {
                    "account_id": accounts[0]["id"],
                    "asset_id": assets[1]["id"],
                    "category_id": categories[2]["id"],
                    "amount": "3000.00",
                    "transaction_type": "INCOME",
                    "description": "工资",
                    "transaction_date": datetime.now().isoformat(),
                },
            ]

            for bill_data in bills_data:
                async with session.post(
                    f"{API_BASE}/bills", json=bill_data, headers=auth_headers
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        bill = data["data"]
                        type_icon = (
                            "💰" if bill["transaction_type"] == "INCOME" else "💸"
                        )
                        print(
                            f"✅ {type_icon} ¥{bill['amount']} - {bill['description']}"
                        )
                    else:
                        error = await response.json()
                        print(f"❌ 创建账单失败: {error}")

        # 7. 生成汇总
        print("\n📊 数据汇总:")
        print("=" * 50)
        print(f"👤 用户: {user_data['username']}")
        print(f"📧 邮箱: {user_data['email']}")
        print(f"🔑 密码: {user_data['password']}")
        print(f"🎫 Token: {access_token[:50]}...")
        print(f"📚 账本: {len(accounts)} 个")
        print(f"💰 资产: {len(assets)} 个")
        print(f"🏷️  分类: {len(categories)} 个")
        print("=" * 50)
        print("✅ Mock数据创建完成！")
        print(f"\n🚀 API文档: {BASE_URL}/docs")


if __name__ == "__main__":
    asyncio.run(create_mock_data())
