"""
账本数据模式
"""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid


class AccountBase(BaseModel):
    """账本基础模式"""

    name: str
    description: Optional[str] = None
    currency: str = "CNY"
    is_shared: bool = False


class AccountCreate(AccountBase):
    """账本创建模式"""

    members: Optional[List[uuid.UUID]] = []


class AccountUpdate(BaseModel):
    """账本更新模式"""

    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    is_shared: Optional[bool] = None
    members: Optional[List[uuid.UUID]] = None


class AccountRead(AccountBase):
    """账本读取模式"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    members: List[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class AccountSummary(BaseModel):
    """账本汇总"""

    total_income: float
    total_expense: float
    net_amount: float
    transaction_count: int
    period: dict
