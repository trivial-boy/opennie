"""
SQL执行服务
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import asyncio

from ..schemas.sql import SQLExecuteResponse, SQLColumnInfo, SQLExecuteError

logger = logging.getLogger(__name__)


class SQLExecutorService:
    """SQL执行服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute_select_query(
        self, 
        sql: str, 
        limit: Optional[int] = 100
    ) -> SQLExecuteResponse:
        """
        执行SELECT查询
        
        Args:
            sql: SQL查询语句
            limit: 结果限制数量
            
        Returns:
            SQL执行响应
            
        Raises:
            SQLAlchemyError: 数据库执行错误
        """
        start_time = time.time()
        
        try:
            # 添加LIMIT子句（如果SQL中没有）
            sql_with_limit = self._add_limit_if_needed(sql, limit)
            
            # 执行查询
            result = await self.db.execute(text(sql_with_limit))
            
            # 获取列信息
            columns = self._get_column_info(result)
            
            # 获取所有行数据
            rows = []
            for row in result:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # 处理特殊数据类型
                    row_dict[column.name] = self._serialize_value(value)
                rows.append(row_dict)
            
            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000
            
            # 检查是否被限制
            limited = len(rows) == limit and limit is not None
            
            logger.info(f"SQL查询执行成功: 返回 {len(rows)} 行, 耗时 {execution_time:.2f}ms")
            
            return SQLExecuteResponse(
                columns=columns,
                rows=rows,
                total_rows=len(rows),
                execution_time_ms=round(execution_time, 2),
                limited=limited
            )
            
        except SQLAlchemyError as e:
            logger.error(f"SQL执行错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise SQLAlchemyError(f"查询执行失败: {str(e)}")
    
    def _add_limit_if_needed(self, sql: str, limit: Optional[int]) -> str:
        """如果SQL中没有LIMIT子句，则添加"""
        if limit is None:
            return sql
            
        sql_lower = sql.lower().strip()
        
        # 检查是否已经有LIMIT子句
        if 'limit' in sql_lower:
            return sql
        
        # 添加LIMIT子句
        return f"{sql.rstrip(';')} LIMIT {limit}"
    
    def _get_column_info(self, result) -> List[SQLColumnInfo]:
        """获取查询结果的列信息"""
        columns = []
        
        if hasattr(result, 'keys') and result.keys():
            for key in result.keys():
                columns.append(SQLColumnInfo(
                    name=str(key),
                    type="unknown"  # SQLAlchemy结果集中很难获取精确的类型信息
                ))
        
        return columns
    
    def _serialize_value(self, value: Any) -> Any:
        """序列化数据库值为JSON可序列化的格式"""
        if value is None:
            return None
        
        # 处理日期时间类型
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        
        # 处理Decimal类型
        if hasattr(value, '__float__'):
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        
        # 处理UUID类型
        if hasattr(value, 'hex'):
            return str(value)
        
        # 处理bytes类型
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return str(value)
        
        # 其他类型直接转字符串
        try:
            return value
        except Exception:
            return str(value)
    
    async def validate_query_safety(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        验证查询的安全性
        
        Returns:
            (是否安全, 错误信息)
        """
        try:
            # 使用EXPLAIN来验证查询语法，但不实际执行
            explain_sql = f"EXPLAIN {sql}"
            await self.db.execute(text(explain_sql))
            return True, None
        except Exception as e:
            return False, f"SQL语法错误: {str(e)}"
    
    async def get_table_info(self) -> Dict[str, List[str]]:
        """获取数据库表信息（用于辅助查询）"""
        try:
            # 获取当前用户可访问的表
            inspector = inspect(self.db.bind)
            
            # 获取表名
            table_names = await asyncio.get_event_loop().run_in_executor(
                None, inspector.get_table_names
            )
            
            table_info = {}
            for table_name in table_names:
                # 获取表的列信息
                columns = await asyncio.get_event_loop().run_in_executor(
                    None, inspector.get_columns, table_name
                )
                table_info[table_name] = [col['name'] for col in columns]
            
            return table_info
            
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}")
            return {}


class SQLQueryHelper:
    """SQL查询助手类 - 提供常用查询模板"""
    
    @staticmethod
    def get_common_queries() -> Dict[str, str]:
        """获取常用查询模板"""
        return {
            "用户统计": """
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN email_verified = true THEN 1 END) as verified_users,
                    DATE(created_at) as registration_date
                FROM users 
                GROUP BY DATE(created_at) 
                ORDER BY registration_date DESC
                LIMIT 10
            """,
            "账单统计": """
                SELECT 
                    type,
                    COUNT(*) as count,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    DATE(date) as bill_date
                FROM bills 
                WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY type, DATE(date)
                ORDER BY bill_date DESC
            """,
            "分类统计": """
                SELECT 
                    c.name as category_name,
                    COUNT(b.id) as transaction_count,
                    SUM(b.amount) as total_amount
                FROM categories c
                LEFT JOIN bills b ON c.id = b.category_id
                WHERE b.date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY c.id, c.name
                ORDER BY total_amount DESC
            """,
            "资产概览": """
                SELECT 
                    type,
                    COUNT(*) as asset_count,
                    SUM(balance) as total_balance
                FROM assets 
                WHERE include_in_total = true
                GROUP BY type
                ORDER BY total_balance DESC
            """
        }
    
    @staticmethod
    def get_table_schemas() -> Dict[str, str]:
        """获取主要表结构信息"""
        return {
            "users": "id, username, email, email_verified, created_at, updated_at",
            "accounts": "id, user_id, name, description, currency, is_shared, created_at",
            "bills": "id, account_id, asset_id, category_id, amount, currency, type, description, date",
            "assets": "id, user_id, name, type, balance, currency, include_in_total",
            "categories": "id, user_id, name, type, icon, color, parent_id",
            "budgets": "id, account_id, name, total_amount, period_type, start_date, end_date",
            "debts": "id, user_id, type, counterpart, amount, currency, due_date, is_settled"
        }