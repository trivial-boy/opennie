#!/usr/bin/env python3
"""
简单的注册测试脚本
"""

import asyncio
import aiohttp
import json


async def test_register():
    """测试注册功能"""

    async with aiohttp.ClientSession() as session:
        # 测试数据
        user_data = {
            "username": "simpletest",
            "email": "simpletest@example.com",
            "password": "123456",
        }

        print("🧪 测试用户注册...")
        print(f"📧 邮箱: {user_data['email']}")
        print(f"👤 用户名: {user_data['username']}")

        try:
            async with session.post(
                "http://localhost:8000/api/v1/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                response_text = await resp.text()
                print(f"📊 状态码: {resp.status}")
                print(f"📝 响应内容: {response_text}")

                if resp.status == 200:
                    data = await resp.json()
                    print("✅ 注册成功!")
                    user_info = data.get("data", {})
                    print(f"🆔 用户ID: {user_info.get('id')}")
                    print(f"📧 邮箱验证: {user_info.get('email_verified')}")
                else:
                    print("❌ 注册失败")

        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_register())
