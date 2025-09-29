"""
数据库工厂 - 根据配置自动选择数据库驱动
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .database import DatabaseManager
    from .database_mysql import DatabaseManager as MySQLDatabaseManager


def get_database_manager():
    """
    根据DATABASE_URL自动选择数据库驱动
    - postgresql+asyncpg:// 使用PostgreSQL + asyncpg
    - mysql+aiomysql:// 使用MySQL + aiomysql
    """
    database_url = os.getenv("DATABASE_URL", "")

    if "mysql" in database_url or "aiomysql" in database_url:
        # 使用MySQL驱动
        from .database_mysql import DatabaseManager as MySQLDatabaseManager
        from .database_mysql import get_database_session, init_database, close_database

        return (
            MySQLDatabaseManager(),
            get_database_session,
            init_database,
            close_database,
        )
    else:
        # 默认使用PostgreSQL驱动
        from .database import DatabaseManager
        from .database import get_database_session, init_database, close_database

        return DatabaseManager(), get_database_session, init_database, close_database


# 自动选择数据库管理器
db_manager, get_database_session, init_database, close_database = get_database_manager()

# 向后兼容性导出
__all__ = ["db_manager", "get_database_session", "init_database", "close_database"]
