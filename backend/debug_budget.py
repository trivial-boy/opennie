#!/usr/bin/env python3
"""
调试预算创建问题
"""

import asyncio
import httpx
import json
from datetime import date, timedelta


BASE_URL = "http://localhost:8000"


async def debug_budget():
    """调试预算创建问题"""
    print("🔍 调试预算创建问题...")

    async with httpx.AsyncClient() as client:
        # 登录
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "test_uswxfh@example.com", "password": "test123"},
        )

        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.text}")
            return

        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")

        # 获取账本
        accounts_response = await client.get(
            f"{BASE_URL}/api/v1/accounts", headers=headers
        )
        accounts = accounts_response.json()["data"]["items"]
        account = accounts[0]
        print(f"✅ 账本: {account['name']} (ID: {account['id']})")

        # 获取分类
        categories_response = await client.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        )
        categories_data = categories_response.json()["data"]
        if isinstance(categories_data, list):
            categories = categories_data
        else:
            categories = categories_data.get("items", categories_data)

        expense_categories = [cat for cat in categories if cat["type"] == "expense"]
        print(f"✅ 找到 {len(expense_categories)} 个支出分类")
        print(
            f"第一个分类: {expense_categories[0]['name']} (ID: {expense_categories[0]['id']})"
        )
        print(
            f"第二个分类: {expense_categories[1]['name']} (ID: {expense_categories[1]['id']})"
        )

        # 尝试创建简单预算
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        simple_budget_data = {
            "account_id": account["id"],
            "name": "简单测试预算",
            "total_amount": "1000.00",
            "period_type": "monthly",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "categories": [],  # 先不加分类
        }

        print("\n🔍 尝试创建简单预算...")
        print(
            f"预算数据: {json.dumps(simple_budget_data, indent=2, ensure_ascii=False)}"
        )

        create_response = await client.post(
            f"{BASE_URL}/api/v1/budgets", headers=headers, json=simple_budget_data
        )

        print(f"响应状态码: {create_response.status_code}")
        print(f"响应内容: {create_response.text}")

        if create_response.status_code != 200:
            # 尝试带分类的预算
            print("\n🔍 尝试创建带分类的预算...")

            budget_with_categories = {
                "account_id": account["id"],
                "name": "带分类的测试预算",
                "total_amount": "2000.00",
                "period_type": "monthly",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "categories": [
                    {
                        "category_id": expense_categories[0]["id"],
                        "allocated_amount": "1000.00",
                    }
                ],
            }

            print(
                f"预算数据: {json.dumps(budget_with_categories, indent=2, ensure_ascii=False)}"
            )

            create_response2 = await client.post(
                f"{BASE_URL}/api/v1/budgets",
                headers=headers,
                json=budget_with_categories,
            )

            print(f"响应状态码: {create_response2.status_code}")
            print(f"响应内容: {create_response2.text}")


if __name__ == "__main__":
    asyncio.run(debug_budget())
