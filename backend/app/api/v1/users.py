"""
用户API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...schemas.user import UserRead, UserUpdate
from ...schemas.common import ResponseModel
from ...models.user import User
from ...api.deps import get_current_user
from sqlalchemy import select

router = APIRouter()


@router.get("/me", response_model=ResponseModel[UserRead], summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return ResponseModel(data=UserRead.from_orm(current_user))


@router.put("/me", response_model=ResponseModel[UserRead], summary="更新当前用户信息")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户信息"""
    # 更新用户信息
    update_data = user_update.dict(exclude_unset=True)

    # 检查用户名是否已被使用
    if "username" in update_data:
        stmt = select(User).where(
            (User.username == update_data["username"]) & (User.id != current_user.id)
        )
        existing_user = await db.execute(stmt)
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="用户名已被使用"
            )

    # 检查邮箱是否已被使用
    if "email" in update_data:
        stmt = select(User).where(
            (User.email == update_data["email"]) & (User.id != current_user.id)
        )
        existing_user = await db.execute(stmt)
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="邮箱已被使用"
            )
        # 如果更改邮箱，需要重新验证
        update_data["email_verified"] = False
        update_data["email_verified_at"] = None

    # 更新用户
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return ResponseModel(
        data=UserRead.from_orm(current_user), message="用户信息更新成功"
    )
