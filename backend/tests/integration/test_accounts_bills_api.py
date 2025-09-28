#!/usr/bin/env python3
"""
账本和账单管理API集成测试账本和账单管理API集成测试
"""

import asyncioasyncio
import httpx
import uuid
import sys
import oshttpx
import uuid
import sys
import os
from datetime import date

# 添加项目路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.core.config import settings

# 添加项目路径
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.core.config import settings

BASE_URL = (
    f"http://localhostlocalhost:{settings.SERVER_PORT}{settings.SERVER_PORT}/api/v1"
)


class AccountsBillsTester:
    def __init__(self):
        self.client = None
        self.test_user = {
            "username": f"accounts_test_{uuid.uuid4().hex[:6]}",
            "email": f"accounts_test_{uuid.uuid4().hex[:6]}@example.com",
            "password": "test123456",
        }
        self.token = None
        self.account_id = None

    async def setup(self):
        """初始化测试"""
        self.client = httpx.AsyncClient()
        print(f"🔧 账本和账单API测试初始化")
        print(f"👤 测试用户: {self.test_user['email']}")

    async def cleanup(self):
        """清理资源"""
        if self.client:
            await self.client.aclose()

    @property
    def headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"}

    async def register_and_login(self):
        """注册并登录"""
        print("\n📝 1. 用户注册和登录...")

        # 注册
        try:
            register_response = await self.client.post(
                f"{BASE_URL}/auth/register", json=self.test_user
            )
        except:
            pass  # 用户可能已存在

        # 登录
        login_response = await self.client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": self.test_user["email"],
                "password": self.test_user["password"],
            },
        )

        if login_response.status_code == 200:
            token_data = login_response.json()
            self.token = token_data["data"]["access_token"]
            print("✅ 用户登录成功")
            return True
        else:
            print(f"❌ 用户登录失败: {login_response.status_code}")
            return False

    async def test_account_management(self):
        """测试账本管理"""
        print("\n📋 2. 测试账本管理...")

        # 创建账本
        account_data = {
            "name": "测试账本",
            "description": "这是一个集成测试账本",
            "currency": "CNY",
            "is_shared": False,
            "members": [],
        }

        response = await self.client.post(
            f"{BASE_URL}/accounts", json=account_data, headers=self.headers
        )

        if response.status_code == 200:
            account = response.json()["data"]
            self.account_id = account["id"]
            print(f"✅ 账本创建成功: {account['name']} (ID: {self.account_id})")

            # 获取账本列表
            response = await self.client.get(
                f"{BASE_URL}/accounts", headers=self.headers
            )
            if response.status_code == 200:
                accounts = response.json()["data"]["items"]
                print(f"✅ 获取账本列表成功，共 {len(accounts)} 个账本")

            # 获取账本详情
            response = await self.client.get(
                f"{BASE_URL}/accounts/{self.account_id}", headers=self.headers
            )
            if response.status_code == 200:
                print("✅ 获取账本详情成功")

            # 更新账本
            update_data = {
                "name": "更新后的测试账本",
                "description": "这是一个更新后的集成测试账本",
            }
            response = await self.client.put(
                f"{BASE_URL}/accounts/{self.account_id}",
                json=update_data,
                headers=self.headers,
            )
            if response.status_code == 200:
                print("✅ 账本更新成功")

            return True
        else:
            print(f"❌ 账本创建失败: {response.status_code}")
            print(response.text)
            return False

    async def test_bill_management(self):
        """测试账单管理"""
        print("\n💰 3. 测试账单管理...")

        if not self.account_id:
            print("❌ 没有可用的账本ID，跳过账单测试")
            return False

        # 获取账单列表（应该为空）
        response = await self.client.get(
            f"{BASE_URL}/bills?account_id={self.account_id}", headers=self.headers
        )

        if response.status_code == 200:
            bills = response.json()["data"]["items"]
            print(f"✅ 获取账单列表成功，共 {len(bills)} 条账单")
        else:
            print(f"❌ 获取账单列表失败: {response.status_code}")
            return False

        # 获取账本汇总
        response = await self.client.get(
            f"{BASE_URL}/accounts/{self.account_id}/summary", headers=self.headers
        )

        if response.status_code == 200:
            summary = response.json()["data"]
            print(f"✅ 获取账本汇总成功:")
            print(f"   总收入: {summary['total_income']}")
            print(f"   总支出: {summary['total_expense']}")
            print(f"   净收入: {summary['net_amount']}")
            print(f"   交易数量: {summary['transaction_count']}")
            return True
        else:
            print(f"❌ 获取账本汇总失败: {response.status_code}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始账本和账单管理API测试")
        print("=" * 50)

        await self.setup()

        test_results = []

        try:
            # 测试用户注册和登录
            result = await self.register_and_login()
            test_results.append(result)
            if not result:
                return False

            # 测试账本管理
            result = await self.test_account_management()
            test_results.append(result)

            # 测试账单管理
            result = await self.test_bill_management()
            test_results.append(result)

        except Exception as e:
            print(f"❌ 测试过程中发生异常: {e}")
            test_results.append(False)

        finally:
            await self.cleanup()

        # 汇总结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")

        test_names = ["用户认证", "账本管理", "账单管理"]
        passed = sum(test_results)
        total = len(test_results)

        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {i + 1}. {name}: {status}")

        print(f"\n🎯 总体结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")

        if passed == total:
            print("🎉 所有账本和账单API测试通过! ✅")
        else:
            print("⚠️ 部分测试失败，请检查相关功能")

        return passed == total


async def main():
    """主函数"""
    tester = AccountsBillsTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
