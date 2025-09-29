"""
通用数据模式 - 统一API响应格式
"""

from typing import Generic, TypeVar, List, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一成功响应模型"""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat() + "Z"})

    success: bool = Field(True, description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field("操作成功", description="响应消息")
    code: int = Field(200, description="状态码")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="响应时间戳"
    )


class PaginationMeta(BaseModel):
    """分页元数据"""

    page: int = Field(..., description="当前页码（从1开始）")
    size: int = Field(..., description="每页大小")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""

    items: List[T] = Field(..., description="数据列表")
    pagination: PaginationMeta = Field(..., description="分页信息")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""

    success: bool = Field(True, description="请求是否成功")
    data: PaginatedData[T] = Field(..., description="分页数据")
    message: str = Field("操作成功", description="响应消息")
    code: int = Field(200, description="状态码")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="响应时间戳"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


class ErrorDetail(BaseModel):
    """错误详情"""

    field: Optional[str] = Field(None, description="错误字段")
    reason: str = Field(..., description="错误原因")


class ErrorInfo(BaseModel):
    """错误信息"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[List[ErrorDetail]] = Field(None, description="错误详情列表")


class ErrorResponse(BaseModel):
    """统一错误响应模型"""

    success: bool = Field(False, description="请求是否成功")
    error: ErrorInfo = Field(..., description="错误信息")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="响应时间戳"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


class MessageResponse(BaseModel):
    """简单消息响应模型"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="响应消息")
    code: int = Field(200, description="状态码")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="响应时间戳"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


# 查询参数基类
class BaseQueryParams(BaseModel):
    """基础查询参数"""

    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(20, ge=1, le=100, description="每页大小，最大100")


class TimeRangeParams(BaseModel):
    """时间范围查询参数"""

    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")


# 响应工具函数
def success_response(
    data: Any = None, message: str = "操作成功", code: int = 200
) -> ResponseModel[Any]:
    """创建成功响应"""
    return ResponseModel(
        success=True, data=data, message=message, code=code, timestamp=datetime.utcnow()
    )


def error_response(
    code: str,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    status_code: int = 400,
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        success=False,
        error=ErrorInfo(code=code, message=message, details=details),
        timestamp=datetime.utcnow(),
    )


def paginated_response(
    items: List[Any], page: int, size: int, total: int, message: str = "操作成功"
) -> PaginatedResponse[Any]:
    """创建分页响应"""
    pages = (total + size - 1) // size if total > 0 else 0

    return PaginatedResponse(
        success=True,
        data=PaginatedData(
            items=items,
            pagination=PaginationMeta(
                page=page,
                size=size,
                total=total,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1,
            ),
        ),
        message=message,
        timestamp=datetime.utcnow(),
    )
