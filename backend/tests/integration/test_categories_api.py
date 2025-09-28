"""
分类API集成测试
"""

import asyncio
import httpx
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from app.core.config import settings


async def test_categories():
    """测试分类功能"""
    print("🚀 开始分类API测试...")

    base_url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/api/v1"

    # 测试用户
    test_user = {
        "username": "category_simple_test",
        "email": "category_simple@example.com",
        "password": "testpassword123",
    }

    async with httpx.AsyncClient() as client:
        # 注册并登录
        try:
            await client.post(f"{base_url}/auth/register", json=test_user)
        except:
            pass  # 用户可能已存在

        login_response = await client.post(
            f"{base_url}/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )

        if login_response.status_code != 200:
            print("❌ 登录失败")
            return

        token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        created_categories = []

        try:
            # 1. 测试创建收入分类
            print("\n1️⃣ 测试创建收入分类...")
            income_data = {
                "name": "工资奖金",
                "type": "income",
                "icon": "💰",
                "color": "#4CAF50",
            }

            response = await client.post(
                f"{base_url}/categories", json=income_data, headers=headers
            )
            assert response.status_code == 200
            income_category = response.json()["data"]
            created_categories.append(income_category["id"])
            print(f"✅ 创建收入分类成功: {income_category['name']}")

            # 2. 测试创建支出分类
            print("\n2️⃣ 测试创建支出分类...")
            expense_data = {
                "name": "生活开销",
                "type": "expense",
                "icon": "🛒",
                "color": "#FF5722",
            }

            response = await client.post(
                f"{base_url}/categories", json=expense_data, headers=headers
            )
            assert response.status_code == 200
            expense_category = response.json()["data"]
            created_categories.append(expense_category["id"])
            print(f"✅ 创建支出分类成功: {expense_category['name']}")

            # 3. 测试创建子分类
            print("\n3️⃣ 测试创建子分类...")
            sub_data = {
                "name": "基本工资",
                "type": "income",
                "icon": "💼",
                "color": "#4CAF50",
                "parent_id": income_category["id"],
            }

            response = await client.post(
                f"{base_url}/categories", json=sub_data, headers=headers
            )
            assert response.status_code == 200
            sub_category = response.json()["data"]
            created_categories.append(sub_category["id"])
            print(f"✅ 创建子分类成功: {sub_category['name']}")

            # 4. 测试获取分类列表
            print("\n4️⃣ 测试获取分类列表...")
            response = await client.get(f"{base_url}/categories", headers=headers)
            assert response.status_code == 200
            categories = response.json()["data"]
            print(f"✅ 获取分类列表成功，共 {len(categories)} 个顶级分类")

            # 5. 测试按类型筛选
            print("\n5️⃣ 测试按类型筛选...")
            response = await client.get(
                f"{base_url}/categories?type=income", headers=headers
            )
            assert response.status_code == 200
            income_categories = response.json()["data"]
            print(f"✅ 筛选收入分类成功，共 {len(income_categories)} 个分类")

            # 6. 测试更新分类
            print("\n6️⃣ 测试更新分类...")
            update_data = {"name": "薪资收入", "color": "#2E7D32"}
            response = await client.put(
                f"{base_url}/categories/{income_category['id']}",
                json=update_data,
                headers=headers,
            )
            assert response.status_code == 200
            updated_category = response.json()["data"]
            assert updated_category["name"] == "薪资收入"
            print(f"✅ 更新分类成功: {updated_category['name']}")

            # 7. 测试删除子分类
            print("\n7️⃣ 测试删除子分类...")
            response = await client.delete(
                f"{base_url}/categories/{sub_category['id']}", headers=headers
            )
            assert response.status_code == 200
            print("✅ 删除子分类成功")
            created_categories.remove(sub_category["id"])

            # 8. 测试验证规则 - 重复名称
            print("\n8️⃣ 测试验证规则...")
            duplicate_data = {
                "name": "薪资收入",  # 与已存在的分类重名
                "type": "income",
                "icon": "💰",
            }
            response = await client.post(
                f"{base_url}/categories", json=duplicate_data, headers=headers
            )
            assert response.status_code == 409  # 应该拒绝重复名称
            print("✅ 重复名称验证通过")

            print("\n🎉 所有分类测试通过！")

        finally:
            # 清理创建的分类
            print("\n🧹 清理测试数据...")
            for category_id in created_categories:
                try:
                    await client.delete(
                        f"{base_url}/categories/{category_id}", headers=headers
                    )
                except:
                    pass
            print("✅ 清理完成")


if __name__ == "__main__":
    asyncio.run(test_categories())
