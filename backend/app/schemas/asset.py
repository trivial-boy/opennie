"""
资产数据模式
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
import uuid
from ..models.asset import AssetTypeEnum


class AssetBase(BaseModel):
    """资产基础模式"""

    name: str
    type: AssetTypeEnum
    balance: Decimal = Decimal("0.00")
    currency: str = "CNY"
    include_in_total: bool = True
    notes: Optional[str] = None


class AssetCreate(AssetBase):
    """资产创建模式"""

    pass


class AssetUpdate(BaseModel):
    """资产更新模式"""

    name: Optional[str] = None
    type: Optional[AssetTypeEnum] = None
    balance: Optional[Decimal] = None
    currency: Optional[str] = None
    include_in_total: Optional[bool] = None
    notes: Optional[str] = None


class AssetRead(AssetBase):
    """资产读取模式"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AssetOverview(BaseModel):
    """资产总览"""

    total_assets: Decimal
    positive_assets: Decimal
    liabilities: Decimal
    net_worth: Decimal
    asset_count: int
    liability_ratio: float
    asset_breakdown: list
