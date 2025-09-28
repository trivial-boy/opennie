"""
分页参数类
"""

from ..core.exceptions import ValidationError


class PaginationParams:
    """分页参数类"""

    def __init__(self, page: int = 1, size: int = 20, max_size: int = 100):
        if page < 1:
            raise ValidationError("页码必须大于0")
        if size < 1:
            raise ValidationError("每页大小必须大于0")
        if size > max_size:
            raise ValidationError(f"每页大小不能超过{max_size}")

        self.page = page
        self.size = size
        self.offset = (page - 1) * size

    def __repr__(self):
        return f"PaginationParams(page={self.page}, size={self.size})"
