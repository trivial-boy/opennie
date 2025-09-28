#!/usr/bin/env python3
"""
创建测试用户
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"


async def create_test_user():
    """创建测试用户"""
    async with httpx.AsyncClient() as client:
        # 注册用户
        register_data = {
            "username": "test",
            "email": "test@example.com",
            "password": "test123",
        }

        print("📝 注册测试用户...")
        register_response = await client.post(
            f"{BASE_URL}/api/v1/auth/register", json=register_data
        )

        print(f"状态码: {register_response.status_code}")
        print(f"响应: {register_response.text}")


if __name__ == "__main__":
    asyncio.run(create_test_user())
