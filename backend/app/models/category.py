"""
分类模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class TransactionTypeEnum(str, enum.Enum):
    """交易类型枚举"""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class Category(Base):
    """分类表"""

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    type = Column(Enum(TransactionTypeEnum), nullable=False, index=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # 颜色代码，如#FF5733
    parent_id = Column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # 父分类ID，支持子分类
    is_system = Column(Boolean, default=False, index=True)  # 是否为系统默认分类
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type}')>"
