"""
债务模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Date, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class DebtTypeEnum(str, enum.Enum):
    """债务类型枚举"""

    BORROW_IN = "borrow_in"  # 借入
    LEND_OUT = "lend_out"  # 借出


class Debt(Base):
    """债务表"""

    __tablename__ = "debts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    type = Column(Enum(DebtTypeEnum), nullable=False, index=True)
    counterpart = Column(String(100), nullable=False)  # 对方姓名或机构
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="CNY")
    description = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True, index=True)
    is_settled = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Debt(id={self.id}, type='{self.type}', counterpart='{self.counterpart}', amount={self.amount})>"
