"""
API依赖项
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from typing import Optional
import uuid

security = HTTPBearer()


async def get_current_user(
    token: str = Depends(security), db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户 - 集成Redis缓存"""
    from ..services.cache import cache_service

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 验证令牌
    payload = await verify_token(token.credentials)
    if payload is None:
        raise credentials_exception

    # 检查令牌类型
    if payload.get("type") != "access":
        raise credentials_exception

    # 获取用户ID
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    # 先尝试从Redis缓存获取用户信息
    cached_user_data = await cache_service.get_cached_user_info(user_id)
    if cached_user_data:
        # 从缓存构建User对象（需要验证缓存数据的有效性）
        try:
            # 仍需要从数据库验证用户存在且状态正确
            stmt = select(User).where(User.id == user_uuid)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                # 缓存数据过期，清除缓存
                await cache_service.invalidate_user_cache(user_id)
                raise credentials_exception

            # 检查缓存数据是否需要更新
            if (
                cached_user_data.get("email") != user.email
                or cached_user_data.get("email_verified") != user.email_verified
            ):
                # 更新缓存
                user_data = {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at.isoformat()
                    if user.created_at
                    else None,
                }
                await cache_service.cache_user_info(user_id, user_data, 3600)

            return user

        except Exception:
            # 缓存处理失败，fallback到数据库查询
            pass

    # 缓存未命中或失败，从数据库查询
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # 缓存用户信息
    try:
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        await cache_service.cache_user_info(user_id, user_data, 3600)
    except Exception as e:
        # 缓存失败不影响正常流程
        import logging

        logging.warning(f"Failed to cache user info: {str(e)}")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户（邮箱已验证）"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱未验证"
        )
    return current_user


def get_optional_current_user():
    """可选的当前用户（允许匿名访问）"""

    async def _get_optional_current_user(
        token: Optional[str] = Depends(security), db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        if not token:
            return None

        try:
            return await get_current_user(token, db)
        except HTTPException:
            return None

    return _get_optional_current_user
