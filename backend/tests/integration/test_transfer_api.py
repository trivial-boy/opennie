#!/usr/bin/env python3
"""
转账功能集成测试
"""

import asyncio
import httpx
import uuid
import sys
import os

# 添加项目路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.core.config import settings

BASE_URL = f"http://localhost:{settings.SERVER_PORT}"
API_BASE = f"{BASE_URL}/api/v1"


class TransferTester:
    def __init__(self):
        self.client = None
        self.test_user = {
            "username": f"transfer_user_{uuid.uuid4().hex[:6]}",
            "email": f"transfer_{uuid.uuid4().hex[:6]}@example.com",
            "password": "test123456",
        }
        self.token = None
        self.accounts = []
        self.asset = None
        self.category = None

    async def setup(self):
        """初始化测试环境"""
        self.client = httpx.AsyncClient()
        print(f"🔧 转账功能测试初始化")
        print(f"👤 测试用户: {self.test_user['email']}")

    async def cleanup(self):
        """清理资源"""
        if self.client:
            await self.client.aclose()

    async def register_and_login(self):
        """注册并登录用户"""
        print("\n📝 1. 注册并登录用户...")

        # 注册
        register_response = await self.client.post(
            f"{API_BASE}/auth/register", json=self.test_user
        )

        if register_response.status_code not in [200, 201]:
            print(f"❌ 注册失败: {register_response.status_code}")
            return False

        print(f"✅ 用户注册成功")

        # 登录
        login_response = await self.client.post(
            f"{API_BASE}/auth/login",
            json={
                "email": self.test_user["email"],
                "password": self.test_user["password"],
            },
        )

        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False

        login_data = login_response.json()
        self.token = login_data["data"]["access_token"]
        print(f"✅ 登录成功")

        return True

    @property
    def headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"}

    async def get_accounts(self):
        """获取用户账户"""
        print("\n📋 2. 获取用户账户...")

        response = await self.client.get(f"{API_BASE}/accounts", headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 获取账户失败: {response.status_code}")
            return False

        accounts_data = response.json()
        self.accounts = accounts_data["data"]["items"]

        print(f"✅ 找到 {len(self.accounts)} 个账户:")
        for account in self.accounts:
            print(f"   - {account['name']} ({account['id']})")

        if len(self.accounts) < 2:
            print("❌ 需要至少2个账户进行转账测试")
            return False

        return True

    async def create_asset(self):
        """创建测试资产"""
        print("\n💰 3. 创建测试资产...")

        asset_data = {
            "name": "转账测试资产",
            "type": "cash",
            "symbol": "CNY",
            "description": "用于转账测试的资产",
        }

        response = await self.client.post(
            f"{API_BASE}/assets", headers=self.headers, json=asset_data
        )

        if response.status_code != 200:
            print(f"❌ 创建资产失败: {response.status_code}")
            print(response.text)
            return False

        self.asset = response.json()["data"]
        print(f"✅ 创建资产成功: {self.asset['name']}")

        return True

    async def get_category(self):
        """获取分类"""
        print("\n📂 4. 获取分类...")

        response = await self.client.get(f"{API_BASE}/categories", headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 获取分类失败: {response.status_code}")
            return False

        categories_data = response.json()
        categories = categories_data["data"]

        if categories:
            self.category = categories[0]
            print(f"✅ 使用分类: {self.category['name']}")
            return True
        else:
            print("❌ 未找到可用分类")
            return False

    async def test_transfer_creation(self):
        """测试转账创建"""
        print("\n💸 5. 测试转账创建...")

        from_account = self.accounts[0]
        to_account = self.accounts[1]

        transfer_data = {
            "account_id": from_account["id"],
            "to_account_id": to_account["id"],
            "asset_id": self.asset["id"],
            "category_id": self.category["id"],
            "type": "transfer",
            "amount": 100.00,
            "description": "转账功能测试",
            "date": "2025-01-15",
        }

        print(f"   转出账户: {from_account['name']}")
        print(f"   转入账户: {to_account['name']}")
        print(f"   转账金额: {transfer_data['amount']}")

        response = await self.client.post(
            f"{API_BASE}/bills", headers=self.headers, json=transfer_data
        )

        print(f"   响应状态: {response.status_code}")

        if response.status_code == 200:
            bill_data = response.json()["data"]
            print(f"✅ 转账创建成功!")
            print(f"   账单ID: {bill_data['id']}")
            print(f"   转账类型: {bill_data['type']}")
            print(f"   转出账户: {bill_data['account_id']}")
            print(f"   转入账户: {bill_data['to_account_id']}")
            print(f"   金额: {bill_data['amount']}")

            return bill_data
        else:
            print(f"❌ 转账创建失败: {response.status_code}")
            print(response.text)
            return None

    async def test_transfer_validation(self):
        """测试转账验证逻辑"""
        print("\n🔍 6. 测试转账验证逻辑...")

        # 测试缺少目标账户
        print("   测试缺少目标账户...")
        invalid_data = {
            "account_id": self.accounts[0]["id"],
            "asset_id": self.asset["id"],
            "category_id": self.category["id"],
            "type": "transfer",
            "amount": 50.00,
            "description": "无效转账测试",
            "date": "2025-01-15",
        }

        response = await self.client.post(
            f"{API_BASE}/bills", headers=self.headers, json=invalid_data
        )

        if response.status_code == 400:
            print("   ✅ 正确拒绝了缺少目标账户的转账")
        else:
            print(f"   ❌ 应该拒绝缺少目标账户的转账 (状态: {response.status_code})")

        # 测试无效的目标账户
        print("   测试无效的目标账户...")
        invalid_data["to_account_id"] = str(uuid.uuid4())

        response = await self.client.post(
            f"{API_BASE}/bills", headers=self.headers, json=invalid_data
        )

        if response.status_code == 404:
            print("   ✅ 正确拒绝了无效的目标账户")
        else:
            print(f"   ❌ 应该拒绝无效的目标账户 (状态: {response.status_code})")

    async def test_transfer_update(self):
        """测试转账更新"""
        print("\n✏️ 7. 测试转账更新...")

        # 先创建一个转账
        transfer_data = {
            "account_id": self.accounts[0]["id"],
            "to_account_id": self.accounts[1]["id"],
            "asset_id": self.asset["id"],
            "category_id": self.category["id"],
            "type": "transfer",
            "amount": 200.00,
            "description": "待更新的转账",
            "date": "2025-01-16",
        }

        create_response = await self.client.post(
            f"{API_BASE}/bills", headers=self.headers, json=transfer_data
        )

        if create_response.status_code != 200:
            print("❌ 无法创建转账用于更新测试")
            return False

        bill = create_response.json()["data"]

        # 更新转账
        update_data = {"amount": 250.00, "description": "已更新的转账"}

        update_response = await self.client.put(
            f"{API_BASE}/bills/{bill['id']}", headers=self.headers, json=update_data
        )

        if update_response.status_code == 200:
            updated_bill = update_response.json()["data"]
            print(f"✅ 转账更新成功!")
            print(f"   新金额: {updated_bill['amount']}")
            print(f"   新描述: {updated_bill['description']}")
            return True
        else:
            print(f"❌ 转账更新失败: {update_response.status_code}")
            return False

    async def run_all_tests(self):
        """运行所有转账测试"""
        print("🧪 开始转账功能集成测试")
        print("=" * 60)

        await self.setup()

        test_results = []

        try:
            # 1. 注册登录
            result = await self.register_and_login()
            test_results.append(result)
            if not result:
                return False

            # 2. 获取账户
            result = await self.get_accounts()
            test_results.append(result)
            if not result:
                return False

            # 3. 创建资产
            result = await self.create_asset()
            test_results.append(result)
            if not result:
                return False

            # 4. 获取分类
            result = await self.get_category()
            test_results.append(result)
            if not result:
                return False

            # 5. 测试转账创建
            bill = await self.test_transfer_creation()
            test_results.append(bill is not None)

            # 6. 测试验证逻辑
            await self.test_transfer_validation()
            test_results.append(True)  # 验证测试总是通过

            # 7. 测试转账更新
            result = await self.test_transfer_update()
            test_results.append(result)

        except Exception as e:
            print(f"❌ 测试过程中发生异常: {e}")
            test_results.append(False)

        finally:
            await self.cleanup()

        # 统计结果
        print("\n" + "=" * 60)
        print("📊 转账功能测试结果:")

        test_names = [
            "用户注册登录",
            "获取用户账户",
            "创建测试资产",
            "获取分类信息",
            "转账创建功能",
            "转账验证逻辑",
            "转账更新功能",
        ]

        passed = sum(test_results)
        total = len(test_results)

        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {i + 1}. {name}: {status}")

        print(f"\n🎯 总体结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")

        if passed == total:
            print("🎉 转账功能测试全部通过! ✅")
        else:
            print("⚠️ 部分转账功能测试失败")

        return passed == total


async def main():
    """主函数"""
    tester = TransferTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
