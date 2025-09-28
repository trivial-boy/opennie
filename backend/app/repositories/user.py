"""
用户Repository实现
"""

from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from .base import BaseRepository
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """用户Repository"""

    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.get_by_field("email", email)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.get_by_field("username", username)

    async def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """根据邮箱或用户名获取用户"""
        stmt = select(User).where(
            or_(User.email == identifier, User.username == identifier)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def is_email_taken(self, email: str, exclude_user_id: UUID = None) -> bool:
        """检查邮箱是否已被使用"""
        stmt = select(User.id).where(User.email == email)
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_username_taken(
        self, username: str, exclude_user_id: UUID = None
    ) -> bool:
        """检查用户名是否已被使用"""
        stmt = select(User.id).where(User.username == username)
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_verified_users(self) -> List[User]:
        """获取已验证邮箱的用户"""
        stmt = select(User).where(User.email_verified == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_unverified_users(self, days_since_creation: int = 7) -> List[User]:
        """获取未验证邮箱的用户"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_since_creation)

        stmt = select(User).where(
            User.email_verified == False, User.created_at < cutoff_date
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_last_login(self, user_id: UUID) -> bool:
        """更新最后登录时间"""
        from datetime import datetime

        user = await self.get(user_id)
        if user:
            # 这里可以添加last_login字段到User模型
            # user.last_login = datetime.utcnow()
            await self.db.flush()
            return True
        return False

    async def verify_email(self, user_id: UUID) -> bool:
        """验证用户邮箱"""
        from datetime import datetime

        user = await self.get(user_id)
        if user:
            user.email_verified = True
            user.email_verified_at = datetime.utcnow()
            await self.db.flush()
            return True
        return False
