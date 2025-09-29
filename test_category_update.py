#!/usr/bin/env python3
"""
测试分类更新功能的脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.services.baidu_ocr import BaiduOCRService
from app.models.category import Category, TransactionTypeEnum
from app.schemas.category import CategoryUpdate
from app.core.database import db
from sqlalchemy import select


async def test_category_update():
    """测试分类更新功能"""
    print("🧪 测试分类更新功能")
    print("=" * 60)

    # 连接数据库
    await db.connect()

    # 创建数据库会话
    async with db.get_session() as session:
        try:
            # 查找一个系统分类
            stmt = select(Category).where(Category.is_system == True).limit(1)
            result = await session.execute(stmt)
            system_category = result.scalar_one_or_none()

            if not system_category:
                print("❌ 没有找到系统分类进行测试")
                return

            print(f"📋 找到系统分类: {system_category.name}")
            print(f"🔧 分类类型: {system_category.type}")
            print(f"🏷️  is_system: {system_category.is_system}")
            print(f"📅 创建时间: {system_category.created_at}")

            # 尝试更新分类名称
            original_name = system_category.name
            new_name = f"{original_name}_修改测试"

            print(f"\n🔄 尝试更新分类名称:")
            print(f"   原名称: {original_name}")
            print(f"   新名称: {new_name}")

            # 模拟更新操作（这里只是测试数据库层面的更新，不经过API验证）
            system_category.name = new_name
            await session.commit()
            await session.refresh(system_category)

            print(f"✅ 更新成功！新名称: {system_category.name}")

            # 恢复原名称
            system_category.name = original_name
            await session.commit()
            await session.refresh(system_category)

            print(f"🔄 已恢复原名称: {system_category.name}")
            print("✅ 系统分类修改功能测试通过！")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(test_category_update())
