#!/usr/bin/env python3
"""
获取访问令牌的简单脚本
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

BASE_URL = f"http://localhost:{settings.SERVER_PORT}"
API_BASE = f"{BASE_URL}/api/v1"


async def get_access_token():
    """获取访问令牌"""

    # 使用已知存在的测试用户凭据
    login_data = {
        "email": "test_uszeob@example.com",  # 从之前的测试输出中获取
        "password": "testpassword123",
    }

    async with aiohttp.ClientSession() as session:
        try:
            print(f"🔑 正在登录获取访问令牌...")
            print(f"📧 用户邮箱: {login_data['email']}")

            async with session.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    login_result = data.get("data", {})
                    access_token = login_result.get("access_token")
                    refresh_token = login_result.get("refresh_token")
                    expires_in = login_result.get("expires_in", 0)

                    print(f"✅ 登录成功!")
                    print(f"🎫 Access Token: {access_token}")
                    print(f"🔄 Refresh Token: {refresh_token}")
                    print(f"⏰ 过期时间: {expires_in}秒 ({expires_in / 60:.1f}分钟)")

                    user_info = login_result.get("user", {})
                    print(
                        f"👤 用户信息: {user_info.get('username')} ({user_info.get('email')})"
                    )

                    return {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": expires_in,
                        "user": user_info,
                    }
                else:
                    data = await resp.json()
                    print(f"❌ 登录失败 (HTTP {resp.status}): {data}")
                    return None

        except Exception as e:
            print(f"❌ 登录请求失败: {str(e)}")
            return None


if __name__ == "__main__":
    result = asyncio.run(get_access_token())
    if result:
        print(f"\n📋 可以使用的Bearer Token:")
        print(f"Authorization: Bearer {result['access_token']}")
    else:
        sys.exit(1)
