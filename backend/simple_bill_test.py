#!/usr/bin/env python3
"""
简单账单创建测试
"""

import asyncio
import aiohttp
import json
from datetime import date

BASE_URL = "http://localhost:8000"


async def test_bill_creation():
    user_data = {"email": "test_uswxfh@example.com", "password": "test123"}

    async with aiohttp.ClientSession() as session:
        # 登录
        async with session.post(
            f"{BASE_URL}/api/v1/auth/login", json=user_data
        ) as resp:
            data = await resp.json()
            token = data["data"]["access_token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 获取现有数据
        async with session.get(f"{BASE_URL}/api/v1/accounts", headers=headers) as resp:
            accounts = (await resp.json())["data"]["items"]

        async with session.get(f"{BASE_URL}/api/v1/assets", headers=headers) as resp:
            assets = (await resp.json())["data"]["items"]

        async with session.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        ) as resp:
            categories = (await resp.json())["data"]

        if accounts and assets and categories:
            # 创建一个简单账单
            bill_data = {
                "account_id": accounts[0]["id"],
                "asset_id": assets[0]["id"],
                "category_id": categories[0]["id"],
                "amount": "25.80",
                "type": "expense",  # 使用正确的字段名
                "description": "测试账单",
                "date": date.today().isoformat(),  # 使用正确的字段名
            }

            print("🧪 测试账单创建...")
            print(f"请求数据: {json.dumps(bill_data, indent=2)}")

            async with session.post(
                f"{BASE_URL}/api/v1/bills", json=bill_data, headers=headers
            ) as resp:
                print(f"响应状态: {resp.status}")
                response_data = await resp.json()
                print(
                    f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}"
                )

        print("\n📊 当前数据汇总:")
        print(f"账本: {len(accounts)} 个")
        print(f"资产: {len(assets)} 个")
        print(f"分类: {len(categories)} 个")


if __name__ == "__main__":
    asyncio.run(test_bill_creation())
