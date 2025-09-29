"""
查询构建器
"""

try:
    from sqlalchemy.sql.selectable import Select
except ImportError:
    # For SQLAlchemy 1.4 compatibility
    from sqlalchemy.sql import Select


class QueryBuilder:
    """查询构建器"""

    def __init__(self, base_query: Select):
        self.base_query = base_query
        self.filters = []
        self.sorts = []

    def filter(self, condition):
        """添加过滤条件"""
        if condition is not None:
            self.filters.append(condition)
        return self

    def filter_by(self, **kwargs):
        """根据字段过滤"""
        for key, value in kwargs.items():
            if value is not None:
                # 这里需要根据具体模型来构建条件
                pass
        return self

    def order_by(self, *columns):
        """添加排序"""
        self.sorts.extend(columns)
        return self

    def build(self) -> Select:
        """构建最终查询"""
        query = self.base_query

        # 应用过滤条件
        for condition in self.filters:
            query = query.where(condition)

        # 应用排序
        if self.sorts:
            query = query.order_by(*self.sorts)

        return query
