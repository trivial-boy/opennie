"""
SQL执行API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
import logging

from ...core.database import get_db
from ...models.user import User
from ...schemas.sql import (
    SQLExecuteRequest, 
    SQLExecuteResponse, 
    SQLExecuteError
)
from ...schemas.common import ResponseModel
from ...services.sql_executor import SQLExecutorService, SQLQueryHelper
from ...api.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/execute",
    response_model=ResponseModel[SQLExecuteResponse],
    summary="执行SQL查询",
    description="执行SELECT查询语句并返回结果。仅支持SELECT语句，具有安全限制。"
)
async def execute_sql_query(
    request: SQLExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    执行SQL查询
    
    安全限制：
    - 仅支持SELECT语句
    - 禁止危险关键词和模式
    - 自动添加结果数量限制
    - 记录查询日志
    """
    try:
        # 创建SQL执行服务
        sql_service = SQLExecutorService(db)
        
        # 验证查询安全性
        is_safe, error_msg = await sql_service.validate_query_safety(request.sql)
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SQL查询验证失败: {error_msg}"
            )
        
        # 执行查询
        result = await sql_service.execute_select_query(
            sql=request.sql,
            limit=request.limit
        )
        
        # 记录查询日志
        logger.info(
            f"用户 {current_user.username} 执行SQL查询: "
            f"{request.sql[:100]}{'...' if len(request.sql) > 100 else ''}"
        )
        
        return ResponseModel(
            data=result,
            message=f"查询执行成功，返回 {result.total_rows} 行结果"
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"SQL执行错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL执行错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.get(
    "/templates",
    response_model=ResponseModel[Dict[str, str]],
    summary="获取常用查询模板",
    description="获取预定义的常用SQL查询模板，可作为查询参考。"
)
async def get_query_templates(
    current_user: User = Depends(get_current_user),
):
    """获取常用查询模板"""
    templates = SQLQueryHelper.get_common_queries()
    
    return ResponseModel(
        data=templates,
        message=f"获取到 {len(templates)} 个查询模板"
    )


@router.get(
    "/schemas",
    response_model=ResponseModel[Dict[str, str]],
    summary="获取数据表结构",
    description="获取主要数据表的字段信息，用于辅助编写SQL查询。"
)
async def get_table_schemas(
    current_user: User = Depends(get_current_user),
):
    """获取数据表结构信息"""
    schemas = SQLQueryHelper.get_table_schemas()
    
    return ResponseModel(
        data=schemas,
        message=f"获取到 {len(schemas)} 个表的结构信息"
    )


@router.get(
    "/tables",
    response_model=ResponseModel[Dict[str, Any]],
    summary="获取数据库表信息",
    description="获取当前数据库中的表名和列信息。"
)
async def get_database_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取数据库表信息"""
    try:
        sql_service = SQLExecutorService(db)
        table_info = await sql_service.get_table_info()
        
        return ResponseModel(
            data=table_info,
            message=f"获取到 {len(table_info)} 个表的信息"
        )
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库信息失败: {str(e)}"
        )


@router.post(
    "/validate",
    response_model=ResponseModel[Dict[str, bool]],
    summary="验证SQL语法",
    description="验证SQL查询语句的语法正确性，不实际执行查询。"
)
async def validate_sql_syntax(
    request: SQLExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """验证SQL语法"""
    try:
        sql_service = SQLExecutorService(db)
        is_valid, error_msg = await sql_service.validate_query_safety(request.sql)
        
        result = {
            "valid": is_valid,
            "error": error_msg
        }
        
        return ResponseModel(
            data=result,
            message="SQL语法验证完成"
        )
        
    except Exception as e:
        logger.error(f"SQL验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL验证失败: {str(e)}"
        )