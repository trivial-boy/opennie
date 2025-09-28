#!/usr/bin/env python3
"""
简单创建测试用户：test / test123
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

BASE_URL = f"http://localhost:{settings.SERVER_PORT}"
API_BASE = f"{BASE_URL}/api/v1"


async def create_test_user():
    """创建test用户并测试登录"""
    user_data = {"username": "test", "email": "test@example.com", "password": "test123"}

    async with aiohttp.ClientSession() as session:
        # 尝试注册
        print("🧪 尝试注册test用户...")
        async with session.post(
            f"{API_BASE}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            response_data = await response.json()
            if response.status == 201:
                print(f"✅ 用户注册成功")
            else:
                print(f"ℹ️  注册响应 ({response.status}): {response_data}")

        # 尝试登录
        print("🔑 尝试登录...")
        login_data = {"email": user_data["email"], "password": user_data["password"]}

        async with session.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            response_data = await response.json()
            if response.status == 200:
                print(f"✅ 登录成功!")
                print(f"🎫 Token: {response_data['data']['access_token'][:50]}...")
                return response_data["data"]["access_token"]
            else:
                print(f"❌ 登录失败 ({response.status}): {response_data}")
                return None


if __name__ == "__main__":
    asyncio.run(create_test_user())
