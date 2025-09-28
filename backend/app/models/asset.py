"""
资产模型
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class AssetTypeEnum(str, enum.Enum):
    """资产类型枚举"""

    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    INVESTMENT = "investment"
    PROPERTY = "property"
    OTHER = "other"


class Asset(Base):
    """资产表"""

    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(AssetTypeEnum), nullable=False, index=True)
    balance = Column(Numeric(15, 2), default=0.00)
    currency = Column(String(3), default="CNY")
    include_in_total = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.type}', balance={self.balance})>"
