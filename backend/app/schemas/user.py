"""
用户数据模式
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """用户基础模式"""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """用户创建模式"""

    password: str


class UserUpdate(BaseModel):
    """用户更新模式"""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class UserRead(UserBase):
    """用户读取模式"""

    id: uuid.UUID
    email_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class UserInDB(UserRead):
    """数据库用户模式（包含敏感信息）"""

    password_hash: str
    email_verified_at: Optional[datetime] = None
