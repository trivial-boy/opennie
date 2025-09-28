"""
账单模型
"""

from sqlalchemy import Column, String, DateTime, Date, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
from .category import TransactionTypeEnum
import uuid


class Bill(Base):
    """账单表"""

    __tablename__ = "bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False, index=True)
    currency = Column(String(3), default="CNY")
    type = Column(Enum(TransactionTypeEnum), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Bill(id={self.id}, amount={self.amount}, type='{self.type}', date={self.date})>"
