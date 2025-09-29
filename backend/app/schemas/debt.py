"""
债务管理相关的Pydantic模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from ..models.debt import DebtTypeEnum


class DebtBase(BaseModel):
    """债务基础模型"""

    type: DebtTypeEnum = Field(..., description="债务类型")
    counterpart: str = Field(
        ..., min_length=1, max_length=100, description="对方姓名或机构"
    )
    amount: Decimal = Field(..., gt=0, description="债务金额")
    currency: str = Field(
        default="CNY", min_length=3, max_length=3, description="货币代码"
    )
    description: Optional[str] = Field(None, max_length=255, description="债务描述")
    due_date: Optional[date] = Field(None, description="到期日期")


class DebtCreate(DebtBase):
    """创建债务请求模型"""

    pass


class DebtUpdate(BaseModel):
    """更新债务请求模型"""

    type: Optional[DebtTypeEnum] = Field(None, description="债务类型")
    counterpart: Optional[str] = Field(
        None, min_length=1, max_length=100, description="对方姓名或机构"
    )
    amount: Optional[Decimal] = Field(None, gt=0, description="债务金额")
    currency: Optional[str] = Field(
        None, min_length=3, max_length=3, description="货币代码"
    )
    description: Optional[str] = Field(None, max_length=255, description="债务描述")
    due_date: Optional[date] = Field(None, description="到期日期")
    is_settled: Optional[bool] = Field(None, description="是否已结清")


class DebtSettle(BaseModel):
    """结清债务请求模型"""

    is_settled: bool = Field(True, description="结清状态")


class DebtResponse(DebtBase):
    """债务响应模型"""

    id: str = Field(..., description="债务ID")
    is_settled: bool = Field(..., description="是否已结清")
    days_until_due: Optional[int] = Field(None, description="距离到期天数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_days(cls, debt_orm):
        """从ORM对象创建响应，计算到期天数"""
        data = debt_orm.__dict__.copy()

        # 转换UUID为字符串
        if "id" in data:
            data["id"] = str(data["id"])

        # 计算距离到期天数
        if debt_orm.due_date and not debt_orm.is_settled:
            from datetime import date

            days_until_due = (debt_orm.due_date - date.today()).days
            data["days_until_due"] = days_until_due
        else:
            data["days_until_due"] = None

        return cls(**data)


class DebtListResponse(BaseModel):
    """债务列表响应模型"""

    items: list[DebtResponse]
    total_borrow_in: Decimal = Field(..., description="总借入金额")
    total_lend_out: Decimal = Field(..., description="总借出金额")
    net_amount: Decimal = Field(..., description="净债务金额(借入-借出)")
    overdue_count: int = Field(..., description="逾期债务数量")
    due_soon_count: int = Field(..., description="即将到期债务数量(7天内)")


class DebtSummary(BaseModel):
    """债务汇总模型"""

    total_borrow_in: Decimal = Field(..., description="总借入金额")
    total_lend_out: Decimal = Field(..., description="总借出金额")
    net_amount: Decimal = Field(..., description="净债务金额")
    settled_count: int = Field(..., description="已结清债务数量")
    unsettled_count: int = Field(..., description="未结清债务数量")
    overdue_count: int = Field(..., description="逾期债务数量")
    due_soon_count: int = Field(..., description="即将到期债务数量")
    average_debt_amount: Decimal = Field(..., description="平均债务金额")


class DebtQueryParams(BaseModel):
    """债务查询参数"""

    type: Optional[DebtTypeEnum] = Field(None, description="债务类型筛选")
    is_settled: Optional[bool] = Field(None, description="结清状态筛选")
    counterpart: Optional[str] = Field(None, description="对方姓名筛选")
    due_date_from: Optional[date] = Field(None, description="到期日期起始")
    due_date_to: Optional[date] = Field(None, description="到期日期结束")
    amount_min: Optional[Decimal] = Field(None, ge=0, description="最小金额")
    amount_max: Optional[Decimal] = Field(None, ge=0, description="最大金额")
    overdue_only: Optional[bool] = Field(False, description="只显示逾期债务")
    due_soon_only: Optional[bool] = Field(False, description="只显示即将到期债务")
