#!/usr/bin/env python3
"""
测试转账功能的简单脚本
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


async def test_transfer_transaction():
    """测试转账交易功能"""
    async with httpx.AsyncClient() as client:
        # 1. 登录获取 token
        # 尝试不同的测试用户凭据
        login_attempts = [
            {"email": "test@example.com", "password": "test123"},
            {"email": "admin@example.com", "password": "admin123"},
            {"email": "user@example.com", "password": "password123"},
        ]

        print("🔑 登录中...")
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login", json=login_data
        )

        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(login_response.text)
            return

        token_data = login_response.json()
        access_token = token_data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        print("✅ 登录成功")

        # 2. 获取用户的账户和资产
        print("\n📋 获取账户列表...")
        accounts_response = await client.get(
            f"{BASE_URL}/api/v1/accounts", headers=headers
        )

        if accounts_response.status_code != 200:
            print(f"❌ 获取账户失败: {accounts_response.status_code}")
            return

        accounts = accounts_response.json()["data"]["items"]
        print(f"✅ 找到 {len(accounts)} 个账户")

        if len(accounts) < 2:
            print("❌ 需要至少2个账户来测试转账")
            return

        from_account = accounts[0]
        to_account = accounts[1]

        print(f"转出账户: {from_account['name']} ({from_account['id']})")
        print(f"转入账户: {to_account['name']} ({to_account['id']})")

        # 3. 获取资产
        print("\n💰 获取资产列表...")
        assets_response = await client.get(f"{BASE_URL}/api/v1/assets", headers=headers)

        if assets_response.status_code != 200:
            print(f"❌ 获取资产失败: {assets_response.status_code}")
            return

        assets = assets_response.json()["data"]["items"]
        print(f"✅ 找到 {len(assets)} 个资产")

        if len(assets) < 1:
            print("❌ 需要至少1个资产来测试转账")
            return

        asset = assets[0]
        print(f"使用资产: {asset['name']} ({asset['id']})")

        # 4. 获取分类
        print("\n📂 获取分类列表...")
        categories_response = await client.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        )

        categories = categories_response.json()["data"]["items"]
        transfer_category = None
        for cat in categories:
            if "转账" in cat["name"] or "transfer" in cat["name"].lower():
                transfer_category = cat
                break

        if not transfer_category:
            transfer_category = categories[0]  # 使用第一个分类

        print(f"使用分类: {transfer_category['name']} ({transfer_category['id']})")

        # 5. 创建转账账单
        print("\n💸 创建转账账单...")
        transfer_data = {
            "account_id": from_account["id"],
            "to_account_id": to_account["id"],
            "asset_id": asset["id"],
            "category_id": transfer_category["id"],
            "type": "transfer",
            "amount": 100.00,
            "description": "测试转账",
            "date": "2025-01-15",
        }

        print(f"转账数据: {json.dumps(transfer_data, indent=2, ensure_ascii=False)}")

        bill_response = await client.post(
            f"{BASE_URL}/api/v1/bills", headers=headers, json=transfer_data
        )

        if bill_response.status_code != 200:
            print(f"❌ 创建转账账单失败: {bill_response.status_code}")
            print(bill_response.text)
            return

        bill_data = bill_response.json()
        print("✅ 转账账单创建成功!")
        print(f"账单ID: {bill_data['data']['id']}")
        print(f"金额: {bill_data['data']['amount']}")
        print(f"描述: {bill_data['data']['description']}")

        # 6. 验证账单详情
        print("\n🔍 验证账单详情...")
        bill_detail_response = await client.get(
            f"{BASE_URL}/api/v1/bills/{bill_data['data']['id']}", headers=headers
        )

        if bill_detail_response.status_code == 200:
            detail_data = bill_detail_response.json()
            print("✅ 账单详情获取成功!")
            print(f"类型: {detail_data['data']['type']}")
            print(f"转出账户: {detail_data['data']['account']['name']}")
            if (
                "to_account_id" in detail_data["data"]
                and detail_data["data"]["to_account_id"]
            ):
                print(f"转入账户ID: {detail_data['data']['to_account_id']}")
        else:
            print(f"❌ 获取账单详情失败: {bill_detail_response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_transfer_transaction())
