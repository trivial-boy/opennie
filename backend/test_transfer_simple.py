#!/usr/bin/env python3
"""
简单的转账功能测试脚本
"""

import asyncio
import httpx
import json
import uuid

BASE_URL = "http://localhost:8000"


async def test_transfer_complete():
    """完整的转账测试流程"""
    async with httpx.AsyncClient() as client:
        # 1. 注册一个新用户
        test_email = f"transfer_test_{uuid.uuid4().hex[:8]}@example.com"
        register_data = {
            "username": f"transfer_user_{uuid.uuid4().hex[:8]}",
            "email": test_email,
            "password": "test123456",
        }

        print("📝 注册新用户...")
        register_response = await client.post(
            f"{BASE_URL}/api/v1/auth/register", json=register_data
        )

        if register_response.status_code not in [200, 201]:
            print(f"❌ 注册失败: {register_response.status_code}")
            print(register_response.text)
            return

        print(f"✅ 用户注册成功: {test_email}")

        # 2. 登录获取token
        login_data = {"email": test_email, "password": "test123456"}

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

        # 3. 获取用户的默认账户和资产
        print("\n📋 获取账户列表...")
        accounts_response = await client.get(
            f"{BASE_URL}/api/v1/accounts", headers=headers
        )

        if accounts_response.status_code != 200:
            print(f"❌ 获取账户失败: {accounts_response.status_code}")
            print(accounts_response.text)
            return

        accounts_data = accounts_response.json()
        accounts = accounts_data["data"]["items"]
        print(f"✅ 找到 {len(accounts)} 个账户")

        if len(accounts) < 2:
            print("❌ 需要至少2个账户来测试转账，当前只有", len(accounts))
            # 显示现有账户
            for acc in accounts:
                print(f"  - {acc['name']} ({acc['id']})")
            return

        from_account = accounts[0]
        to_account = accounts[1]

        print(f"转出账户: {from_account['name']} ({from_account['id']})")
        print(f"转入账户: {to_account['name']} ({to_account['id']})")

        # 4. 创建测试资产
        print("\n💰 创建测试资产...")
        asset_data = {
            "name": "人民币现金",
            "type": "cash",
            "symbol": "CNY",
            "description": "用于转账测试的现金资产",
        }

        asset_response = await client.post(
            f"{BASE_URL}/api/v1/assets", headers=headers, json=asset_data
        )

        if asset_response.status_code != 200:
            print(f"❌ 创建资产失败: {asset_response.status_code}")
            print(asset_response.text)
            return

        asset = asset_response.json()["data"]
        print(f"✅ 创建资产成功: {asset['name']} ({asset['id']})")

        # 5. 获取分类列表
        print("\n📂 获取分类列表...")
        categories_response = await client.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        )

        if categories_response.status_code != 200:
            print(f"❌ 获取分类失败: {categories_response.status_code}")
            print(categories_response.text)
            return

        categories_data = categories_response.json()
        print(f"分类API响应: {categories_data}")

        # 检查响应结构
        if isinstance(categories_data, list):
            categories = categories_data
        elif "data" in categories_data:
            if isinstance(categories_data["data"], list):
                categories = categories_data["data"]
            elif "items" in categories_data["data"]:
                categories = categories_data["data"]["items"]
            else:
                categories = []
        else:
            categories = []
        print(f"✅ 找到 {len(categories)} 个分类")

        # 寻找转账相关分类，或使用第一个
        transfer_category = categories[0] if categories else None
        if not transfer_category:
            print("❌ 未找到可用分类")
            return

        print(f"使用分类: {transfer_category['name']} ({transfer_category['id']})")

        # 6. 创建转账账单
        print("\n💸 创建转账账单...")
        transfer_data = {
            "account_id": from_account["id"],
            "to_account_id": to_account["id"],
            "asset_id": asset["id"],
            "category_id": transfer_category["id"],
            "type": "transfer",
            "amount": 100.00,
            "description": "测试转账交易",
            "date": "2025-01-15",
        }

        print(f"转账数据: {json.dumps(transfer_data, indent=2, ensure_ascii=False)}")

        bill_response = await client.post(
            f"{BASE_URL}/api/v1/bills", headers=headers, json=transfer_data
        )

        print(f"响应状态码: {bill_response.status_code}")
        print(f"响应内容: {bill_response.text}")

        if bill_response.status_code == 200:
            bill_data = bill_response.json()
            print("✅ 转账账单创建成功!")
            print(f"账单ID: {bill_data['data']['id']}")
            print(f"金额: {bill_data['data']['amount']}")
            print(f"类型: {bill_data['data']['type']}")
            print(f"描述: {bill_data['data']['description']}")

            # 验证转账字段
            if "to_account_id" in bill_data["data"]:
                print(f"转入账户ID: {bill_data['data']['to_account_id']}")
            else:
                print("⚠️ 响应中未包含 to_account_id 字段")

        else:
            print(f"❌ 创建转账账单失败: {bill_response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_transfer_complete())
