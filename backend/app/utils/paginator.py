"""
分页器类
"""

from typing import List, TypeVar, Generic, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

try:
    from sqlalchemy.sql.selectable import Select
except ImportError:
    # For SQLAlchemy 1.4 compatibility
    from sqlalchemy.sql import Select

from ..schemas.common import PaginatedResponse, PaginationMeta, PaginatedData
from .pagination_params import PaginationParams

T = TypeVar("T")


class Paginator(Generic[T]):
    """分页器"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def paginate(
        self,
        query: Select,
        params: PaginationParams,
        transform_func: Optional[callable] = None,
    ) -> tuple[List[Any], PaginationMeta]:
        """
        执行分页查询

        Args:
            query: SQLAlchemy查询对象
            params: 分页参数
            transform_func: 数据转换函数（如转换为Pydantic模型）

        Returns:
            (数据列表, 分页元数据)
        """
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        total = result.scalar() or 0

        # 获取分页数据
        paginated_query = query.offset(params.offset).limit(params.size)
        result = await self.session.execute(paginated_query)
        items = result.scalars().all()

        # 数据转换
        if transform_func:
            items = [transform_func(item) for item in items]

        # 创建分页元数据
        pages = (total + params.size - 1) // params.size if total > 0 else 0
        pagination_meta = PaginationMeta(
            page=params.page,
            size=params.size,
            total=total,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )

        return items, pagination_meta

    async def paginate_response(
        self,
        query: Select,
        params: PaginationParams,
        transform_func: Optional[callable] = None,
        message: str = "操作成功",
    ) -> PaginatedResponse[Any]:
        """
        执行分页查询并返回标准响应格式
        """
        items, pagination_meta = await self.paginate(query, params, transform_func)

        return PaginatedResponse(
            success=True,
            data=PaginatedData(items=items, pagination=pagination_meta),
            message=message,
            code=200,
        )
