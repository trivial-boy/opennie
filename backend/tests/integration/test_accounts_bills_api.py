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

# 配置
BASE_URL = "http://192.168.0.173:8000/api/v1"
headers = {"Content-Type": "application/json"}


def test_user_registration_and_login():
    """测试用户注册和登录"""
    print("=== 测试用户注册和登录 ===")

    # 注册用户
    register_data = {
        "username": "test_user_accounts",
        "email": "testaccounts@example.com",
        "password": "test123456",
    }

    response = requests.post(
        f"{BASE_URL}/auth/register", json=register_data, headers=headers
    )
    print(f"注册响应: {response.status_code}")
    if response.status_code == 201:
        print("✅ 用户注册成功")
    else:
        print(f"❌ 用户注册失败: {response.text}")

    # 登录获取token
    login_data = {"email": "testaccounts@example.com", "password": "test123456"}

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["data"]["access_token"]
        print("✅ 用户登录成功")
        return access_token
    else:
        print(f"❌ 用户登录失败: {response.text}")
        return None


def test_account_management(token):
    """测试账本管理"""
    print("\n=== 测试账本管理 ===")

    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # 创建账本
    account_data = {
        "name": "我的测试账本",
        "description": "这是一个测试账本",
        "currency": "CNY",
        "is_shared": False,
        "members": [],
    }

    response = requests.post(
        f"{BASE_URL}/accounts", json=account_data, headers=auth_headers
    )

    if response.status_code == 200:
        account = response.json()["data"]
        account_id = account["id"]
        print(f"✅ 账本创建成功: {account['name']} (ID: {account_id})")

        # 获取账本列表
        response = requests.get(f"{BASE_URL}/accounts", headers=auth_headers)
        if response.status_code == 200:
            accounts = response.json()["data"]["items"]
            print(f"✅ 获取账本列表成功，共 {len(accounts)} 个账本")

        # 获取账本详情
        response = requests.get(
            f"{BASE_URL}/accounts/{account_id}", headers=auth_headers
        )
        if response.status_code == 200:
            print("✅ 获取账本详情成功")

        # 更新账本
        update_data = {
            "name": "我的更新测试账本",
            "description": "这是一个更新后的测试账本",
        }
        response = requests.put(
            f"{BASE_URL}/accounts/{account_id}", json=update_data, headers=auth_headers
        )
        if response.status_code == 200:
            print("✅ 账本更新成功")

        return account_id
    else:
        print(f"❌ 账本创建失败: {response.text}")
        return None


def test_bill_management(token, account_id):
    """测试账单管理"""
    print("\n=== 测试账单管理 ===")

    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # 注意：这里需要有效的asset_id和category_id
    # 在实际使用中，需要先创建资产和分类
    print("⚠️  账单创建需要先创建资产和分类，当前仅展示API调用流程")

    # 获取账单列表（空列表）
    response = requests.get(
        f"{BASE_URL}/bills?account_id={account_id}", headers=auth_headers
    )

    if response.status_code == 200:
        bills = response.json()["data"]["items"]
        print(f"✅ 获取账单列表成功，共 {len(bills)} 条账单")
    else:
        print(f"❌ 获取账单列表失败: {response.text}")

    # 获取账本汇总
    response = requests.get(
        f"{BASE_URL}/accounts/{account_id}/summary", headers=auth_headers
    )

    if response.status_code == 200:
        summary = response.json()["data"]
        print(f"✅ 获取账本汇总成功:")
        print(f"   总收入: {summary['total_income']}")
        print(f"   总支出: {summary['total_expense']}")
        print(f"   净收入: {summary['net_amount']}")
        print(f"   交易数量: {summary['transaction_count']}")
    else:
        print(f"❌ 获取账本汇总失败: {response.text}")


def main():
    """主测试函数"""
    print("开始测试账本和账单管理API...")

    # 测试用户注册和登录
    token = test_user_registration_and_login()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        return

    # 测试账本管理
    account_id = test_account_management(token)
    if not account_id:
        print("❌ 无法创建账本，跳过账单测试")
        return

    # 测试账单管理
    test_bill_management(token, account_id)

    print("\n✅ 所有API测试完成！")


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
