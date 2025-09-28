"""
用户会话模型
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class UserSession(Base):
    """用户会话表"""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    device_info = Column(String(255), nullable=True)
    ip_address = Column(INET, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
