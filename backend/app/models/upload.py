"""
文件上传模型
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
import enum


class FileTypeEnum(str, enum.Enum):
    """文件类型枚举"""

    IMAGE = "image"
    VOICE = "voice"
    CSV = "csv"
    OTHER = "other"


class Upload(Base):
    """文件上传记录表"""

    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(Enum(FileTypeEnum), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)  # 文件大小(字节)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<Upload(id={self.id}, file_name='{self.file_name}', file_type='{self.file_type}')>"
