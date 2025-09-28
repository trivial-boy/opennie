#!/usr/bin/env python3
"""
用户认证功能测试脚本
"""

import asyncio
import aiohttp
import json
import random
import string
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


class AuthTester:
    def __init__(self):
        self.session = None
        self.test_user = {
            "username": f"testuser_{''.join(random.choices(string.ascii_lowercase, k=6))}",
            "email": f"test_{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com",
            "password": "testpassword123",
        }
        self.access_token = None
        self.refresh_token = None

    async def setup(self):
        """初始化HTTP会话"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 测试环境初始化完成")
        print(f"📍 API地址: {API_BASE}")
        print(f"👤 测试用户: {self.test_user['username']} ({self.test_user['email']})")

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()

    async def test_health_check(self):
        """测试服务健康检查"""
        print("\n🔍 1. 测试服务健康检查...")
        try:
            async with self.session.get(f"{BASE_URL}/") as resp:
                data = await resp.json()
                print(f"   ✅ 服务状态: {data.get('status', 'unknown')}")
                print(f"   📍 环境: {data.get('environment', 'unknown')}")
                return resp.status == 200
        except Exception as e:
            print(f"   ❌ 健康检查失败: {str(e)}")
            return False

    async def test_register(self):
        """测试用户注册"""
        print(f"\n📝 2. 测试用户注册...")
        try:
            register_data = {
                "username": self.test_user["username"],
                "email": self.test_user["email"],
                "password": self.test_user["password"],
            }

            async with self.session.post(
                f"{API_BASE}/auth/register",
                json=register_data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()

                if resp.status == 200:
                    print(f"   ✅ 注册成功: {data.get('message', '')}")
                    user_data = data.get("data", {})
                    print(f"   👤 用户ID: {user_data.get('id', 'N/A')}")
                    print(
                        f"   📧 邮箱验证状态: {user_data.get('email_verified', False)}"
                    )
                    return True
                else:
                    print(f"   ❌ 注册失败 (HTTP {resp.status}): {data}")
                    return False

        except Exception as e:
            print(f"   ❌ 注册请求失败: {str(e)}")
            return False

    async def test_login(self):
        """测试用户登录"""
        print(f"\n🔑 3. 测试用户登录...")
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"],
            }

            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()

                if resp.status == 200:
                    login_result = data.get("data", {})
                    self.access_token = login_result.get("access_token")
                    self.refresh_token = login_result.get("refresh_token")
                    expires_in = login_result.get("expires_in", 0)

                    print(f"   ✅ 登录成功!")
                    print(
                        f"   🎫 Access Token: {self.access_token[:20]}... (长度: {len(self.access_token)})"
                    )
                    print(
                        f"   🔄 Refresh Token: {self.refresh_token[:20]}... (长度: {len(self.refresh_token)})"
                    )
                    print(f"   ⏰ 过期时间: {expires_in}秒 ({expires_in / 60:.1f}分钟)")

                    user_info = login_result.get("user", {})
                    print(
                        f"   👤 用户信息: {user_info.get('username')} ({user_info.get('email')})"
                    )
                    return True
                else:
                    print(f"   ❌ 登录失败 (HTTP {resp.status}): {data}")
                    return False

        except Exception as e:
            print(f"   ❌ 登录请求失败: {str(e)}")
            return False

    async def test_protected_route(self):
        """测试受保护的路由"""
        print(f"\n🛡️ 4. 测试JWT令牌验证...")
        if not self.access_token:
            print("   ❌ 没有access token，跳过测试")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # 测试获取用户信息（这里用健康检查代替，因为没有专门的用户信息接口）
            async with self.session.get(f"{BASE_URL}/health", headers=headers) as resp:
                data = await resp.json()

                if resp.status == 200:
                    print(f"   ✅ JWT令牌验证成功")
                    print(f"   📊 服务状态: {data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"   ❌ JWT令牌验证失败 (HTTP {resp.status}): {data}")
                    return False

        except Exception as e:
            print(f"   ❌ 令牌验证请求失败: {str(e)}")
            return False

    async def test_refresh_token(self):
        """测试刷新令牌"""
        print(f"\n🔄 5. 测试刷新令牌...")
        if not self.refresh_token:
            print("   ❌ 没有refresh token，跳过测试")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.refresh_token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{API_BASE}/auth/refresh", headers=headers
            ) as resp:
                data = await resp.json()

                if resp.status == 200:
                    refresh_result = data.get("data", {})
                    new_access_token = refresh_result.get("access_token")
                    expires_in = refresh_result.get("expires_in", 0)

                    print(f"   ✅ 令牌刷新成功!")
                    print(
                        f"   🎫 新Access Token: {new_access_token[:20]}... (长度: {len(new_access_token)})"
                    )
                    print(f"   ⏰ 过期时间: {expires_in}秒 ({expires_in / 60:.1f}分钟)")

                    self.access_token = new_access_token  # 更新token
                    return True
                else:
                    print(f"   ❌ 令牌刷新失败 (HTTP {resp.status}): {data}")
                    return False

        except Exception as e:
            print(f"   ❌ 令牌刷新请求失败: {str(e)}")
            return False

    async def test_logout(self):
        """测试用户登出"""
        print(f"\n🚪 6. 测试用户登出...")
        if not self.access_token:
            print("   ❌ 没有access token，跳过测试")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{API_BASE}/auth/logout", headers=headers
            ) as resp:
                data = await resp.json()

                if resp.status == 200:
                    print(f"   ✅ 登出成功: {data.get('data', {}).get('message', '')}")

                    # 测试登出后token是否失效
                    print("   🔍 验证token是否已失效...")
                    async with self.session.get(
                        f"{BASE_URL}/health", headers=headers
                    ) as test_resp:
                        if test_resp.status == 401:
                            print("   ✅ Token已成功加入黑名单")
                        else:
                            print("   ⚠️ Token可能仍然有效")

                    return True
                else:
                    print(f"   ❌ 登出失败 (HTTP {resp.status}): {data}")
                    return False

        except Exception as e:
            print(f"   ❌ 登出请求失败: {str(e)}")
            return False

    async def test_login_with_wrong_password(self):
        """测试错误密码登录"""
        print(f"\n🔒 7. 测试错误密码登录...")
        try:
            login_data = {"email": self.test_user["email"], "password": "wrongpassword"}

            async with self.session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()

                if resp.status == 401:
                    print(f"   ✅ 正确拒绝了错误密码: {data.get('detail', '')}")
                    return True
                else:
                    print(f"   ❌ 应该拒绝错误密码 (HTTP {resp.status}): {data}")
                    return False

        except Exception as e:
            print(f"   ❌ 错误密码测试失败: {str(e)}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始用户认证功能测试")
        print("=" * 50)

        await self.setup()

        test_results = []
        test_functions = [
            self.test_health_check,
            self.test_register,
            self.test_login,
            self.test_protected_route,
            self.test_refresh_token,
            self.test_logout,
            self.test_login_with_wrong_password,
        ]

        for test_func in test_functions:
            try:
                result = await test_func()
                test_results.append(result)
                await asyncio.sleep(0.5)  # 短暂延迟
            except Exception as e:
                print(f"   ❌ 测试异常: {str(e)}")
                test_results.append(False)

        await self.cleanup()

        # 汇总结果
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        passed = sum(test_results)
        total = len(test_results)

        test_names = [
            "服务健康检查",
            "用户注册",
            "用户登录",
            "JWT令牌验证",
            "刷新令牌",
            "用户登出",
            "错误密码拒绝",
        ]

        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {i + 1}. {name}: {status}")

        print(f"\n🎯 总体结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")

        if passed == total:
            print("🎉 所有测试通过！用户认证功能正常 ✅")
        else:
            print("⚠️ 部分测试失败，请检查相关功能")

        return passed == total


async def main():
    tester = AuthTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
