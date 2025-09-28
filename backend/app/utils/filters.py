"""
过滤器构建器
"""

from typing import Optional, List


class FilterBuilder:
    """过滤器构建器"""

    @staticmethod
    def text_filter(column, value: Optional[str], exact: bool = False):
        """文本过滤"""
        if not value:
            return None

        if exact:
            return column == value
        else:
            return column.ilike(f"%{value}%")

    @staticmethod
    def date_range_filter(column, start_date=None, end_date=None):
        """日期范围过滤"""
        conditions = []

        if start_date:
            conditions.append(column >= start_date)

        if end_date:
            conditions.append(column <= end_date)

        return conditions

    @staticmethod
    def enum_filter(column, value):
        """枚举过滤"""
        if not value:
            return None
        return column == value

    @staticmethod
    def numeric_range_filter(column, min_value=None, max_value=None):
        """数值范围过滤"""
        conditions = []

        if min_value is not None:
            conditions.append(column >= min_value)

        if max_value is not None:
            conditions.append(column <= max_value)

        return conditions

    @staticmethod
    def in_filter(column, values: Optional[List]):
        """IN过滤"""
        if not values:
            return None
        return column.in_(values)

    @staticmethod
    def boolean_filter(column, value: Optional[bool]):
        """布尔值过滤"""
        if value is None:
            return None
        return column == value
