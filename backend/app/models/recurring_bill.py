"""
周期账单模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Date, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class FrequencyEnum(str, enum.Enum):
    """频率枚举"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RecurringBill(Base):
    """周期账单表（订阅、分期）"""

    __tablename__ = "recurring_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_bill_id = Column(UUID(as_uuid=True), nullable=False)  # 模板账单ID
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="CNY")
    asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    frequency = Column(Enum(FrequencyEnum), nullable=False, index=True)
    next_due_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<RecurringBill(id={self.id}, name='{self.name}', frequency='{self.frequency}')>"
