"""
AI对话模型
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class AIConversation(Base):
    """AI对话记录表"""

    __tablename__ = "ai_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # 会话ID
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=True)  # 生成的SQL查询语句
    query_result = Column(JSONB, nullable=True)  # SQL查询结果
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AIConversation(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"
