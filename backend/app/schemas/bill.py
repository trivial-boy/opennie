"""
账单数据模式
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
import uuid
from ..models.category import TransactionTypeEnum


class BillBase(BaseModel):
    """账单基础模式"""

    account_id: uuid.UUID
    asset_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    currency: str = "CNY"
    type: TransactionTypeEnum
    description: Optional[str] = None
    date: date


class BillCreate(BillBase):
    """账单创建模式"""

    pass


class BillUpdate(BaseModel):
    """账单更新模式"""

    account_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    type: Optional[TransactionTypeEnum] = None
    description: Optional[str] = None
    date: Optional[date] = None


class BillRead(BillBase):
    """账单读取模式"""

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BillWithDetails(BillRead):
    """带详情的账单模式"""

    account: dict
    asset: dict
    category: dict


class DailySummary(BaseModel):
    """每日汇总"""

    date: date
    total_income: Decimal
    total_expense: Decimal
    net_amount: Decimal
    transaction_count: int
    bills: List[dict]
