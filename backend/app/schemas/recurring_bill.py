"""
周期账单相关的Pydantic模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from ..models.recurring_bill import FrequencyEnum


class RecurringBillBase(BaseModel):
    """周期账单基础模型"""

    name: str = Field(..., min_length=1, max_length=100, description="周期账单名称")
    amount: Decimal = Field(..., gt=0, description="账单金额")
    currency: str = Field(
        default="CNY", min_length=3, max_length=3, description="货币代码"
    )
    asset_id: str = Field(..., description="关联资产ID")
    category_id: str = Field(..., description="关联分类ID")
    frequency: FrequencyEnum = Field(..., description="执行频率")
    next_due_date: date = Field(..., description="下次执行日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    description: Optional[str] = Field(None, max_length=255, description="描述")


class RecurringBillCreate(RecurringBillBase):
    """创建周期账单请求模型"""

    pass


class RecurringBillUpdate(BaseModel):
    """更新周期账单请求模型"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="周期账单名称"
    )
    amount: Optional[Decimal] = Field(None, gt=0, description="账单金额")
    currency: Optional[str] = Field(
        None, min_length=3, max_length=3, description="货币代码"
    )
    asset_id: Optional[str] = Field(None, description="关联资产ID")
    category_id: Optional[str] = Field(None, description="关联分类ID")
    frequency: Optional[FrequencyEnum] = Field(None, description="执行频率")
    next_due_date: Optional[date] = Field(None, description="下次执行日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    description: Optional[str] = Field(None, max_length=255, description="描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class RecurringBillResponse(RecurringBillBase):
    """周期账单响应模型"""

    id: str = Field(..., description="周期账单ID")
    user_id: str = Field(..., description="用户ID")
    template_bill_id: str = Field(..., description="模板账单ID")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 关联信息
    asset: Optional[dict] = Field(None, description="关联资产信息")
    category: Optional[dict] = Field(None, description="关联分类信息")

    model_config = {"from_attributes": True}


class RecurringBillExecute(BaseModel):
    """执行周期账单请求模型"""

    execution_date: Optional[date] = Field(None, description="执行日期，默认为当前日期")
    amount: Optional[Decimal] = Field(
        None, gt=0, description="执行金额，默认为周期账单金额"
    )
    description: Optional[str] = Field(None, max_length=255, description="本次执行描述")


class RecurringBillToggle(BaseModel):
    """切换周期账单状态请求模型"""

    is_active: bool = Field(..., description="是否激活")


class RecurringBillSummary(BaseModel):
    """周期账单汇总统计"""

    total_count: int = Field(..., description="总周期账单数")
    active_count: int = Field(..., description="活跃周期账单数")
    inactive_count: int = Field(..., description="非活跃周期账单数")
    total_monthly_amount: Decimal = Field(..., description="预计月度总金额")
    due_soon_count: int = Field(..., description="即将到期数量(7天内)")
    overdue_count: int = Field(..., description="已逾期数量")
    next_due_date: Optional[date] = Field(None, description="最近到期日期")
    frequency_distribution: dict = Field(..., description="频率分布统计")
