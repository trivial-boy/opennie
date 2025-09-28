"""
数据库连接管理 - 使用SQLAlchemy 1.4稳定版本
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
    """简化的数据库管理器 - 使用asyncpg连接池"""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._is_connected = False

    async def connect(self):
        """连接数据库"""
        if self._is_connected:
            return

        # 创建异步引擎 - asyncpg是PostgreSQL最佳异步驱动
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            # asyncpg连接池配置 - 这些都是经过验证的最佳实践
            pool_size=10,  # 连接池大小
            max_overflow=20,  # 最大溢出连接
            pool_timeout=30,  # 获取连接超时(秒)
            pool_recycle=3600,  # 连接回收时间(1小时)
            pool_pre_ping=True,  # 连接前测试(防止断线)
            echo=settings.is_development,  # 开发环境显示SQL
            future=True,  # 使用SQLAlchemy 2.0风格API
        )

        # 创建异步会话工厂
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # 测试连接
        await self._test_connection()
        self._is_connected = True

        logger.info("✅ PostgreSQL数据库连接成功 (asyncpg驱动)")

    async def _test_connection(self):
        """测试数据库连接"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(
                    f"🐘 PostgreSQL: {version.split()[1] if version else 'Unknown'}"
                )
        except Exception as e:
            logger.error(f"❌ 数据库连接测试失败: {e}")
            raise

    async def disconnect(self):
        """断开数据库连接"""
        if not self._is_connected:
            return

        if self.engine:
            await self.engine.dispose()

        self._is_connected = False
        logger.info("✅ 数据库连接已关闭")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话上下文管理器"""
        if not self._is_connected:
            raise RuntimeError("数据库未连接，请先调用 connect()")

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def check_health(self) -> dict:
        """数据库健康检查"""
        try:
            if not self._is_connected:
                return {"status": "disconnected", "message": "数据库未连接"}

            async with self.get_session() as session:
                # 基础连接测试
                result = await session.execute(text("SELECT 1 as test"))
                if result.scalar() != 1:
                    return {"status": "unhealthy", "message": "连接测试失败"}

                # 获取数据库版本信息
                version_result = await session.execute(text("SELECT version()"))
                version = version_result.scalar()

                # 获取连接池状态
                pool = self.engine.pool

                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "version": version.split()[1] if version else "unknown",
                    "driver": "asyncpg",
                    "connection_pool": {
                        "size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "total_connections": pool.size() + pool.overflow(),
                    },
                }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected


# 全局数据库管理器实例
db = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入 - 获取数据库会话"""
    async with db.get_session() as session:
        yield session


# 别名，供API路由使用
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入 - 获取数据库会话 (别名)"""
    async with db.get_session() as session:
        yield session


async def create_tables():
    """创建数据库表"""
    # 导入所有存在的模型以确保它们被注册到Base.metadata
    from ..models import (
        user,
        account,
        asset,
        category,
        bill,
        budget,
        debt,
        upload,
        ai_conversation,
        user_session,
        email_verification,
        recurring_bill,
    )

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ 数据库表创建成功")


async def drop_tables():
    """删除所有数据库表"""
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("✅ 数据库表删除成功")


async def init_database():
    """初始化数据库连接"""
    await db.connect()

    # 开发环境自动创建表
    if settings.is_development:
        await create_tables()
        logger.info("✅ 开发环境表结构已创建")

    logger.info("🗄️ 数据库初始化完成")


async def close_database():
    """关闭数据库连接"""
    await db.disconnect()
    logger.info("🗄️ 数据库已关闭")


# 健康检查辅助函数
async def check_database_health() -> dict:
    """数据库健康检查 - 供外部调用"""
    return await db.check_health()
