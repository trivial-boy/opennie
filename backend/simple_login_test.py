#!/usr/bin/env python3
"""
简单的用户登录测试
"""

import asyncio
import aiohttp
import json


async def test_login():
    """测试用户登录"""
    url = "http://localhost:8000/api/v1/auth/login"

    # 测试数据
    login_data = {"email": "test@example.com", "password": "testpassword123"}

    async with aiohttp.ClientSession() as session:
        try:
            print("🔑 测试用户登录...")
            print(f"📧 邮箱: {login_data['email']}")
            print(f"🔒 密码: {login_data['password']}")

            async with session.post(url, json=login_data) as response:
                status = response.status
                data = await response.json()

                print(f"\n📊 响应状态: {status}")
                print(f"📄 响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")

                if status == 200 and data.get("success"):
                    print("✅ 登录成功！")
                    if "data" in data and "access_token" in data["data"]:
                        print(f"🎫 访问令牌: {data['data']['access_token'][:50]}...")
                    return True
                else:
                    print("❌ 登录失败")
                    return False

        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False


if __name__ == "__main__":
    asyncio.run(test_login())
