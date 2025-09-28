"""
分类数据模式
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid
from ..models.category import TransactionTypeEnum


class CategoryBase(BaseModel):
    """分类基础模式"""

    name: str
    type: TransactionTypeEnum
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class CategoryCreate(CategoryBase):
    """分类创建模式"""

    pass


class CategoryUpdate(BaseModel):
    """分类更新模式"""

    name: Optional[str] = None
    type: Optional[TransactionTypeEnum] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class CategoryRead(CategoryBase):
    """分类读取模式"""

    id: uuid.UUID
    user_id: uuid.UUID
    is_system: bool
    created_at: datetime
    updated_at: datetime
    children: Optional[List["CategoryRead"]] = []

    class Config:
        from_attributes = True
