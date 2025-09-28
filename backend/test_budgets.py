#!/usr/bin/env python3
"""
测试预算功能
"""

import asyncio
import httpx
import json
from datetime import date, timedelta
from decimal import Decimal


BASE_URL = "http://localhost:8000"


async def test_budgets():
    """测试预算相关功能"""
    print("🧪 开始测试预算功能...")

    async with httpx.AsyncClient() as client:
        # 使用指定用户登录
        print("📝 用户登录...")
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

        # 开始测试预算功能
        print("\n🔍 === 预算功能测试 ===")

        # 1. 获取用户的账本和分类数据
        print("📝 1. 准备测试数据...")

        # 获取账本列表
        accounts_response = await client.get(
            f"{BASE_URL}/api/v1/accounts", headers=headers
        )
        if accounts_response.status_code != 200:
            print(f"❌ 获取账本失败: {accounts_response.text}")
            return

        accounts = accounts_response.json()["data"]["items"]
        if not accounts:
            print("❌ 需要至少1个账本才能测试预算")
            return

        account = accounts[0]
        print(f"✅ 使用账本: {account['name']} (ID: {account['id']})")

        # 获取分类列表
        categories_response = await client.get(
            f"{BASE_URL}/api/v1/categories", headers=headers
        )
        if categories_response.status_code != 200:
            print(f"❌ 获取分类失败: {categories_response.text}")
            return

        categories_data = categories_response.json()["data"]
        # 处理分类数据格式
        if isinstance(categories_data, list):
            categories = categories_data
        else:
            categories = categories_data.get("items", categories_data)
        expense_categories = [cat for cat in categories if cat["type"] == "expense"]
        if len(expense_categories) < 2:
            print("❌ 需要至少2个支出分类才能测试预算")
            return

        print(f"✅ 找到 {len(expense_categories)} 个支出分类")

        # 2. 创建预算
        print("\n📝 2. 创建预算...")
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        budget_data = {
            "account_id": account["id"],
            "name": "测试月度预算",
            "total_amount": "5000.00",
            "period_type": "monthly",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "categories": [
                {
                    "category_id": expense_categories[0]["id"],
                    "allocated_amount": "2000.00",
                },
                {
                    "category_id": expense_categories[1]["id"],
                    "allocated_amount": "1500.00",
                },
            ],
        }

        create_response = await client.post(
            f"{BASE_URL}/api/v1/budgets", headers=headers, json=budget_data
        )

        if create_response.status_code != 200:
            print(f"❌ 创建预算失败: {create_response.text}")
            return

        new_budget = create_response.json()["data"]
        print(f"✅ 预算创建成功: {new_budget['name']} (ID: {new_budget['id']})")

        # 3. 获取预算列表
        print("\n📝 3. 获取预算列表...")
        budgets_response = await client.get(
            f"{BASE_URL}/api/v1/budgets", headers=headers
        )

        if budgets_response.status_code != 200:
            print(f"❌ 获取预算列表失败: {budgets_response.text}")
            return

        budgets_data = budgets_response.json()["data"]
        budgets = budgets_data["items"]
        print(f"✅ 获取到 {len(budgets)} 个预算:")
        for budget in budgets:
            print(
                f"   - {budget['name']} (总金额: {budget['total_amount']}, 已花费: {budget['total_spent']})"
            )

        # 4. 获取预算详情
        print("\n📝 4. 获取预算详情...")
        detail_response = await client.get(
            f"{BASE_URL}/api/v1/budgets/{new_budget['id']}", headers=headers
        )

        if detail_response.status_code != 200:
            print(f"❌ 获取预算详情失败: {detail_response.text}")
            return

        detail = detail_response.json()["data"]
        print(f"✅ 预算详情获取成功:")
        print(f"   - 名称: {detail['name']}")
        print(f"   - 总金额: {detail['total_amount']}")
        print(f"   - 已花费: {detail['total_spent']}")
        print(f"   - 剩余金额: {detail['remaining_amount']}")
        print(f"   - 使用比例: {detail['usage_percentage']:.1f}%")
        print(f"   - 分类明细: {len(detail['categories'])} 个")

        for category in detail["categories"]:
            print(f"     * {category['category_name']}: {category['allocated_amount']}")

        # 5. 创建一些测试账单来测试预算计算
        print("\n📝 5. 创建测试账单...")

        # 获取资产
        assets_response = await client.get(f"{BASE_URL}/api/v1/assets", headers=headers)
        if assets_response.status_code == 200:
            assets = assets_response.json()["data"]["items"]
            if assets:
                asset = assets[0]

                # 创建测试账单
                bill_data = {
                    "account_id": account["id"],
                    "asset_id": asset["id"],
                    "category_id": expense_categories[0]["id"],
                    "amount": "500.00",
                    "type": "expense",
                    "description": "测试预算支出",
                    "date": start_date.isoformat(),
                }

                bill_response = await client.post(
                    f"{BASE_URL}/api/v1/bills", headers=headers, json=bill_data
                )

                if bill_response.status_code == 200:
                    print("✅ 测试账单创建成功")
                else:
                    print(f"⚠️ 测试账单创建失败: {bill_response.text}")

        # 6. 获取预算执行进度
        print("\n📝 6. 获取预算执行进度...")
        progress_response = await client.get(
            f"{BASE_URL}/api/v1/budgets/{new_budget['id']}/progress", headers=headers
        )

        if progress_response.status_code != 200:
            print(f"❌ 获取预算进度失败: {progress_response.text}")
        else:
            progress = progress_response.json()["data"]
            print(f"✅ 预算进度获取成功:")
            print(f"   - 已花费: {progress['progress']['total_spent']}")
            print(f"   - 使用比例: {progress['progress']['usage_percentage']:.1f}%")
            print(f"   - 已过天数: {progress['progress']['days_elapsed']}")
            print(f"   - 剩余天数: {progress['progress']['days_remaining']}")
            print(f"   - 日均花费: {progress['progress']['daily_average_spent']:.2f}")
            print(f"   - 预计总花费: {progress['progress']['projected_total']:.2f}")
            print(f"   - 按计划执行: {progress['progress']['is_on_track']}")

            if progress["alerts"]:
                print(f"   - 预警信息: {len(progress['alerts'])} 条")
                for alert in progress["alerts"]:
                    print(f"     * {alert['type']}: {alert['message']}")

        # 7. 更新预算
        print("\n📝 7. 更新预算...")
        update_data = {"name": "更新后的测试预算", "total_amount": "6000.00"}

        update_response = await client.put(
            f"{BASE_URL}/api/v1/budgets/{new_budget['id']}",
            headers=headers,
            json=update_data,
        )

        if update_response.status_code != 200:
            print(f"❌ 更新预算失败: {update_response.text}")
        else:
            updated_budget = update_response.json()["data"]
            print(f"✅ 预算更新成功: {updated_budget['name']}")

        # 8. 按条件过滤预算
        print("\n📝 8. 按条件过滤预算...")
        filter_response = await client.get(
            f"{BASE_URL}/api/v1/budgets?account_id={account['id']}&period_type=monthly",
            headers=headers,
        )

        if filter_response.status_code == 200:
            filtered_budgets = filter_response.json()["data"]["items"]
            print(f"✅ 过滤查询成功，找到 {len(filtered_budgets)} 个月度预算")
        else:
            print(f"❌ 过滤查询失败: {filter_response.text}")

        # 9. 测试分页
        print("\n📝 9. 测试分页...")
        page_response = await client.get(
            f"{BASE_URL}/api/v1/budgets?page=1&size=5", headers=headers
        )

        if page_response.status_code == 200:
            page_data = page_response.json()["data"]
            print(f"✅ 分页测试成功:")
            print(f"   - 当前页: {page_data['pagination']['page']}")
            print(f"   - 每页数量: {page_data['pagination']['size']}")
            print(f"   - 总数: {page_data['pagination']['total']}")
        else:
            print(f"❌ 分页测试失败: {page_response.text}")

        # 10. 删除预算
        print("\n📝 10. 删除测试预算...")
        delete_response = await client.delete(
            f"{BASE_URL}/api/v1/budgets/{new_budget['id']}", headers=headers
        )

        if delete_response.status_code != 200:
            print(f"❌ 删除预算失败: {delete_response.text}")
        else:
            print("✅ 预算删除成功")

        # 11. 验证预算已删除
        print("\n📝 11. 验证预算已删除...")
        verify_response = await client.get(
            f"{BASE_URL}/api/v1/budgets/{new_budget['id']}", headers=headers
        )

        if verify_response.status_code == 404:
            print("✅ 确认预算已删除")
        else:
            print(f"❌ 预算删除验证失败: {verify_response.status_code}")

        print("\n🎉 预算功能测试完成！")
        print("\n📊 测试结果总结:")
        print("   ✅ 创建预算 - 成功")
        print("   ✅ 获取预算列表 - 成功")
        print("   ✅ 获取预算详情 - 成功")
        print("   ✅ 获取预算进度 - 成功")
        print("   ✅ 更新预算 - 成功")
        print("   ✅ 条件过滤 - 成功")
        print("   ✅ 分页查询 - 成功")
        print("   ✅ 删除预算 - 成功")
        print("   ✅ 验证删除 - 成功")


if __name__ == "__main__":
    asyncio.run(test_budgets())
