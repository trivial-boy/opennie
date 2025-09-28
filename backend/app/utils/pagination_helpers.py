"""
分页便捷函数
"""

from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select
from ..schemas.common import PaginatedResponse, PaginationMeta
from .pagination_params import PaginationParams
from .paginator import Paginator


async def paginate_query(
    session: AsyncSession,
    query: Select,
    page: int = 1,
    size: int = 20,
    transform_func: Optional[callable] = None,
) -> tuple[List[Any], PaginationMeta]:
    """便捷的分页查询函数"""
    params = PaginationParams(page, size)
    paginator = Paginator(session)
    return await paginator.paginate(query, params, transform_func)


async def paginate_response(
    session: AsyncSession,
    query: Select,
    page: int = 1,
    size: int = 20,
    transform_func: Optional[callable] = None,
    message: str = "操作成功",
) -> PaginatedResponse[Any]:
    """便捷的分页响应函数"""
    params = PaginationParams(page, size)
    paginator = Paginator(session)
    return await paginator.paginate_response(query, params, transform_func, message)
