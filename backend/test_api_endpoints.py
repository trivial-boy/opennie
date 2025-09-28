#!/usr/bin/env python3
"""
测试API端点是否可用
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"


async def test_endpoints():
    print("🔍 测试API端点可用性...")

    # 测试用户：testuser_uswxfh / test123
    user_data = {"email": "test_uswxfh@example.com", "password": "test123"}

    async with aiohttp.ClientSession() as session:
        # 登录获取token
        print("🔑 登录...")
        async with session.post(
            f"{BASE_URL}/api/v1/auth/login", json=user_data
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data["data"]["access_token"]
                print(f"✅ 登录成功")
            else:
                print(f"❌ 登录失败: {await resp.json()}")
                return

        headers = {"Authorization": f"Bearer {token}"}

        # 测试各个端点
        endpoints = [
            ("GET", "/api/v1/accounts", "账本列表"),
            ("GET", "/api/v1/assets", "资产列表"),
            ("GET", "/api/v1/categories", "分类列表"),
            ("GET", "/api/v1/bills", "账单列表"),
        ]

        for method, url, desc in endpoints:
            async with session.request(
                method, f"{BASE_URL}{url}", headers=headers
            ) as resp:
                print(f"\n{desc} ({method} {url}):")
                print(f"  状态码: {resp.status}")

                try:
                    data = await resp.json()
                    print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    text = await resp.text()
                    print(f"  响应: {text}")

        # 测试创建账本
        print(f"\n📚 测试创建账本:")
        account_data = {
            "name": "测试账本",
            "description": "测试用账本",
            "currency": "CNY",
        }

        async with session.post(
            f"{BASE_URL}/api/v1/accounts",
            json=account_data,
            headers={**headers, "Content-Type": "application/json"},
        ) as resp:
            print(f"  状态码: {resp.status}")
            try:
                data = await resp.json()
                print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                text = await resp.text()
                print(f"  响应: {text}")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
