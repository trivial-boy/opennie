"""
数据库连接管理 - MySQL版本使用aiomysql
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# 创建基础模型类 - SQLAlchemy 1.4语法
Base = declarative_base()


class DatabaseManager:
    """数据库管理器 - MySQL版本使用aiomysql"""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._is_connected = False

    async def connect(self):
        """连接数据库"""
        if self._is_connected:
            return

        # 创建异步引擎 - aiomysql是MySQL最佳异步驱动
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            # aiomysql连接池配置
            pool_size=10,  # 连接池大小
            max_overflow=20,  # 最大溢出连接
            pool_timeout=30,  # 获取连接超时(秒)
            pool_recycle=3600,  # 连接回收时间(1小时)
            pool_pre_ping=True,  # 连接前测试(防止断线)
            echo=settings.is_development,  # 开发环境显示SQL
            future=True,  # 使用SQLAlchemy 2.0风格API
            # MySQL特定配置
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
                "init_command": "SET time_zone='+08:00'",
            },
        )

        # 创建异步会话工厂
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._is_connected = True
        logger.info("✅ MySQL数据库连接已建立")

    async def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            await self.engine.dispose()
            self._is_connected = False
            logger.info("📴 MySQL数据库连接已断开")

    async def create_tables(self):
        """创建数据库表"""
        if not self.engine:
            await self.connect()

        # 导入所有模型以确保表被创建
        from ..models import (
            user,
            account,
            asset,
            category,
            bill,
            budget,
            debt,
            recurring_bill,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("📋 MySQL数据库表创建完成")

    async def check_connection(self):
        """检查数据库连接状态"""
        if not self.engine:
            return False

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"❌ MySQL数据库连接检查失败: {e}")
            return False

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self.session_factory:
            await self.connect()

        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ 数据库事务回滚: {e}")
                raise
            finally:
                await session.close()

    async def get_connection_info(self) -> dict:
        """获取连接信息"""
        if not self.engine:
            return {"connected": False}

        try:
            pool = self.engine.pool
            return {
                "connected": self._is_connected,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
        except Exception as e:
            logger.error(f"❌ 获取MySQL连接信息失败: {e}")
            return {"connected": False, "error": str(e)}


# 创建全局数据库管理器实例
db_manager = DatabaseManager()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取数据库会话"""
    async with db_manager.get_session() as session:
        yield session


# 生命周期管理
async def init_database():
    """初始化数据库"""
    await db_manager.connect()
    await db_manager.create_tables()


async def close_database():
    """关闭数据库连接"""
    await db_manager.disconnect()
