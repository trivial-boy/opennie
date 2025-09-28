"""
预算数据模式
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
import uuid
from ..models.budget import PeriodTypeEnum


class BudgetBase(BaseModel):
    """预算基础模式"""

    account_id: uuid.UUID
    name: str
    total_amount: Decimal
    period_type: PeriodTypeEnum
    start_date: date
    end_date: date


class BudgetCreate(BudgetBase):
    """预算创建模式"""

    categories: Optional[List["BudgetCategoryCreate"]] = []


class BudgetUpdate(BaseModel):
    """预算更新模式"""

    name: Optional[str] = None
    total_amount: Optional[Decimal] = None
    period_type: Optional[PeriodTypeEnum] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class BudgetRead(BudgetBase):
    """预算读取模式"""

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetCategoryCreate(BaseModel):
    """预算分类创建模式"""

    category_id: uuid.UUID
    allocated_amount: Decimal


class BudgetCategoryRead(BaseModel):
    """预算分类读取模式"""

    id: uuid.UUID
    budget_id: uuid.UUID
    category_id: uuid.UUID
    allocated_amount: Decimal
    spent_amount: Decimal
    category_name: Optional[str] = None
    remaining_amount: Decimal = Decimal("0.00")
    usage_percentage: float = 0.0

    class Config:
        from_attributes = True


class BudgetWithCategories(BudgetRead):
    """带分类的预算模式"""

    categories: List[BudgetCategoryRead]
    total_spent: Decimal
    remaining_amount: Decimal
    usage_percentage: float


class BudgetProgress(BaseModel):
    """预算执行进度"""

    budget: BudgetRead
    progress: dict
    categories: List[BudgetCategoryRead]
    alerts: List[dict]
