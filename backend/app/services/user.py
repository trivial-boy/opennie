"""
用户服务层
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..repositories.user import UserRepository
from ..schemas.user import UserCreate, UserUpdate, UserRead
from ..core.security import get_password_hash, verify_password
from .base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate, UserRead]):
    """用户业务逻辑服务"""

    def __init__(self, session: AsyncSession):
        repository = UserRepository(session)
        super().__init__(repository, UserRead)
        self.session = session

    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = await self.get_by_username(user_data.username)
        if existing_user:
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        existing_email = await self.get_by_email(user_data.email)
        if existing_email:
            raise ValueError("邮箱已存在")

        # 创建用户
        user_dict = user_data.dict()
        user_dict["password_hash"] = get_password_hash(user_data.password)
        del user_dict["password"]  # 移除明文密码

        return await self.create(user_dict)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = await self.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """更新用户密码"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.password_hash = get_password_hash(new_password)
        await self.session.commit()
        return True

    async def verify_email(self, user_id: str) -> bool:
        """验证用户邮箱"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.email_verified = True
        await self.session.commit()
        return True

    async def search_users(
        self, keyword: str, page: int = 1, size: int = 20
    ) -> tuple[List[User], int]:
        """搜索用户"""
        query = select(User).where(
            User.username.ilike(f"%{keyword}%") | User.email.ilike(f"%{keyword}%")
        )

        return await self.repository.paginate(query, page, size)
