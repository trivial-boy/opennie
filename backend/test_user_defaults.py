#!/usr/bin/env python3
"""
测试用户注册时的默认数据创建
"""

import asyncio
import aiohttp
import json
import random
import string

BASE_URL = "http://localhost:8000"


async def test_user_registration_defaults():
    print("🧪 测试用户注册默认数据创建")
    print("=" * 50)

    # 生成随机用户信息
    random_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
    user_data = {
        "username": f"newuser_{random_suffix}",
        "email": f"newuser_{random_suffix}@example.com",
        "password": "test123456",
    }

    print(f"👤 测试用户: {user_data['username']}")
    print(f"📧 邮箱: {user_data['email']}")

    async with aiohttp.ClientSession() as session:
        # 1. 注册新用户
        print("\n📝 用户注册...")
        async with session.post(
            f"{BASE_URL}/api/v1/auth/register", json=user_data
        ) as resp:
            if resp.status in [200, 201]:
                register_data = await resp.json()
                print(f"✅ 注册成功: {register_data['message']}")
                user_id = register_data["data"]["id"]
                print(f"🆔 用户ID: {user_id}")
            else:
                error_data = await resp.json()
                print(f"❌ 注册失败: {error_data}")
                return

        # 2. 登录获取token
        print("\n🔑 用户登录...")
        login_data = {"email": user_data["email"], "password": user_data["password"]}

        async with session.post(
            f"{BASE_URL}/api/v1/auth/login", json=login_data
        ) as resp:
            if resp.status == 200:
                login_response = await resp.json()
                token = login_response["data"]["access_token"]
                print(f"✅ 登录成功")
            else:
                error_data = await resp.json()
                print(f"❌ 登录失败: {error_data}")
                return

        headers = {"Authorization": f"Bearer {token}"}

        # 3. 检查默认账本
        print("\n📚 检查默认账本...")
        async with session.get(f"{BASE_URL}/api/v1/accounts", headers=headers) as resp:
            if resp.status == 200:
                accounts_data = await resp.json()
                accounts = accounts_data["data"]["items"]
                print(f"✅ 账本数量: {len(accounts)}")
                for account in accounts:
                    print(f"  📖 {account['name']}: {account['description']}")
            else:
                print(f"❌ 获取账本失败: {await resp.json()}")

        # 4. 检查默认分类
        print("\n🏷️ 检查默认分类...")
        async with session.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        ) as resp:
            if resp.status == 200:
                categories_data = await resp.json()
                categories = categories_data["data"]
                print(f"✅ 分类数量: {len(categories)}")

                # 按类型分组显示
                expense_cats = [c for c in categories if c.get("type") == "expense"]
                income_cats = [c for c in categories if c.get("type") == "income"]

                print(f"  💸 支出分类 ({len(expense_cats)}个):")
                for cat in expense_cats[:5]:  # 只显示前5个
                    icon = cat.get("icon", "")
                    print(f"    {icon} {cat['name']}")
                if len(expense_cats) > 5:
                    print(f"    ... 还有 {len(expense_cats) - 5} 个分类")

                print(f"  💰 收入分类 ({len(income_cats)}个):")
                for cat in income_cats:
                    icon = cat.get("icon", "")
                    print(f"    {icon} {cat['name']}")
            else:
                print(f"❌ 获取分类失败: {await resp.json()}")

        # 5. 检查是否可以正常创建账单
        print("\n📝 测试账单创建...")
        if len(accounts) > 0 and len(categories) > 0:
            # 创建一个现金资产用于测试
            asset_data = {"name": "现金", "type": "cash", "balance": "1000.00"}

            async with session.post(
                f"{BASE_URL}/api/v1/assets", json=asset_data, headers=headers
            ) as resp:
                if resp.status in [200, 201]:
                    asset = (await resp.json())["data"]
                    print(f"✅ 创建测试资产: {asset['name']}")

                    # 创建测试账单
                    bill_data = {
                        "account_id": accounts[0]["id"],
                        "asset_id": asset["id"],
                        "category_id": expense_cats[0]["id"]
                        if expense_cats
                        else categories[0]["id"],
                        "amount": "50.00",
                        "type": "expense",
                        "description": "测试支出",
                        "date": "2025-09-29",
                    }

                    async with session.post(
                        f"{BASE_URL}/api/v1/bills", json=bill_data, headers=headers
                    ) as resp:
                        if resp.status in [200, 201]:
                            bill = (await resp.json())["data"]
                            print(
                                f"✅ 创建测试账单: ¥{bill['amount']} - {bill['description']}"
                            )
                        else:
                            print(f"❌ 创建账单失败: {await resp.json()}")

        # 6. 最终汇总
        print("\n📊 注册默认数据汇总:")
        print("=" * 50)
        print(f"👤 用户: {user_data['username']}")
        print(f"🔑 密码: {user_data['password']}")
        print(f"📚 默认账本: {len(accounts)} 个")
        print(f"🏷️ 默认分类: {len(categories)} 个")
        print(f"  - 支出分类: {len(expense_cats)} 个")
        print(f"  - 收入分类: {len(income_cats)} 个")
        print("✅ 用户可以立即开始记账！")


if __name__ == "__main__":
    asyncio.run(test_user_registration_defaults())
