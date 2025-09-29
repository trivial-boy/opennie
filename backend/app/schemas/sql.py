"""
SQL执行相关的数据模式
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import re


class SQLExecuteRequest(BaseModel):
    """SQL执行请求"""
    
    sql: str = Field(..., description="要执行的SQL语句", min_length=1, max_length=10000)
    limit: Optional[int] = Field(default=100, description="结果限制数量", ge=1, le=1000)
    
    @validator('sql')
    def validate_sql(cls, v):
        """验证SQL语句安全性"""
        sql_lower = v.lower().strip()
        
        # 只允许SELECT语句
        if not sql_lower.startswith('select'):
            raise ValueError("只允许执行SELECT查询语句")
        
        # 禁止的关键词
        forbidden_keywords = [
            'drop', 'delete', 'update', 'insert', 'alter', 'create',
            'truncate', 'grant', 'revoke', 'exec', 'execute',
            'sp_', 'xp_', 'pg_', 'information_schema'
        ]
        
        for keyword in forbidden_keywords:
            if keyword in sql_lower:
                raise ValueError(f"SQL语句包含禁止的关键词: {keyword}")
        
        # 检查是否包含危险字符
        dangerous_patterns = [
            r'--',  # SQL注释
            r'/\*',  # SQL注释开始
            r'\*/',  # SQL注释结束
            r';.*select',  # 多语句执行
            r'union.*select',  # UNION注入（除非是合法的）
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_lower):
                raise ValueError(f"SQL语句包含可能危险的模式")
        
        return v


class SQLColumnInfo(BaseModel):
    """SQL查询结果列信息"""
    
    name: str = Field(..., description="列名")
    type: str = Field(..., description="数据类型")


class SQLExecuteResponse(BaseModel):
    """SQL执行响应"""
    
    columns: List[SQLColumnInfo] = Field(..., description="列信息")
    rows: List[Dict[str, Any]] = Field(..., description="查询结果行")
    total_rows: int = Field(..., description="总行数")
    execution_time_ms: float = Field(..., description="执行时间(毫秒)")
    limited: bool = Field(default=False, description="结果是否被限制")


class SQLExecuteError(BaseModel):
    """SQL执行错误"""
    
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误信息")
    sql_state: Optional[str] = Field(None, description="SQL状态码")