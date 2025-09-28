"""
排序构建器
"""

from typing import List


class SortBuilder:
    """排序构建器"""

    @staticmethod
    def parse_sort_string(sort_str: str, model_class: type) -> List:
        """
        解析排序字符串

        格式: "field1:asc,field2:desc"
        """
        if not sort_str:
            return []

        sorts = []
        for item in sort_str.split(","):
            parts = item.strip().split(":")
            field_name = parts[0]
            direction = parts[1] if len(parts) > 1 else "asc"

            if hasattr(model_class, field_name):
                column = getattr(model_class, field_name)
                if direction.lower() == "desc":
                    sorts.append(column.desc())
                else:
                    sorts.append(column.asc())

        return sorts

    @staticmethod
    def default_sort(model_class: type, field: str = "created_at", desc: bool = True):
        """默认排序"""
        if hasattr(model_class, field):
            column = getattr(model_class, field)
            return [column.desc() if desc else column.asc()]
        return []
