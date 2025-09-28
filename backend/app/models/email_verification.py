"""
邮箱验证模型
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class EmailVerification(Base):
    """邮箱验证表"""

    __tablename__ = "email_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    email = Column(String(100), nullable=False, index=True)
    verification_code = Column(String(6), nullable=False, index=True)
    verification_token = Column(String(255), nullable=False, unique=True, index=True)
    type = Column(
        String(20), nullable=False, default="registration"
    )  # 'registration', 'password_reset'
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<EmailVerification(id={self.id}, email='{self.email}', type='{self.type}')>"
