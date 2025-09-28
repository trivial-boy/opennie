"""
认证API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash,
)
from ...schemas.auth import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    VerifyEmailRequest,
    SendVerificationRequest,
)
from ...schemas.user import UserRead
from ...schemas.common import ResponseModel
from ...models.user import User
from ...models.email_verification import EmailVerification
from sqlalchemy import select
from datetime import datetime, timedelta

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=ResponseModel[UserRead], summary="用户注册")
async def register(user_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册

    - **username**: 用户名（唯一）
    - **email**: 邮箱地址（唯一）
    - **password**: 密码
    """
    # 检查用户是否已存在
    stmt = select(User).where(
        (User.email == user_data.email) | (User.username == user_data.username)
    )
    existing_user = await db.execute(stmt)
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已存在"
        )

    # 创建用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        # 如果邮件验证被禁用，直接设置为已验证
        email_verified=not settings.EMAIL_VERIFICATION_ENABLED,
        email_verified_at=datetime.utcnow()
        if not settings.EMAIL_VERIFICATION_ENABLED
        else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 根据配置决定是否发送验证邮件
    if settings.EMAIL_VERIFICATION_ENABLED:
        # 发送验证邮件
        from ...services.email_verification import email_verification_service

        try:
            await email_verification_service.send_verification_email(
                db=db,
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                verification_type="registration",
            )
            message = "注册成功，验证邮件已发送到您的邮箱，请查收并验证邮箱后登录"
        except Exception as e:
            message = f"注册成功，但验证邮件发送失败: {str(e)}"
    else:
        message = "注册成功，可以直接登录"

    return ResponseModel(
        data=UserRead.from_orm(user),
        message=message,
    )


@router.post("/login", response_model=ResponseModel[LoginResponse], summary="用户登录")
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录

    - **email**: 邮箱地址
    - **password**: 密码
    """
    from ...services.cache import cache_service

    # 检查登录尝试次数
    login_attempts = await cache_service.get_login_attempts(credentials.email)
    max_attempts = 5  # 最大尝试次数

    if login_attempts >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过多，请15分钟后再试",
        )

    # 先尝试从缓存获取用户信息
    user = None
    cached_user = await cache_service.get_cached_user_info(f"email:{credentials.email}")

    if cached_user:
        # 从缓存获取用户信息
        user_id = cached_user.get("id")
        if user_id:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

    if not user:
        # 缓存未命中，从数据库查询
        stmt = select(User).where(User.email == credentials.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # 缓存用户信息（如果用户存在）
        if user:
            user_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            await cache_service.cache_user_info(f"email:{user.email}", user_data, 3600)
            await cache_service.cache_user_info(str(user.id), user_data, 3600)

    # 验证用户和密码
    password_valid = False
    if user:
        try:
            password_valid = verify_password(credentials.password, user.password_hash)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            password_valid = False

    if not user or not password_valid:
        # 增加失败尝试次数
        await cache_service.increment_login_attempts(credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
        )

    # 检查邮箱是否已验证（只有在邮件验证启用时才检查）
    if settings.EMAIL_VERIFICATION_ENABLED and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="邮箱未验证，请先验证邮箱后登录",
        )

    # 登录成功，重置失败尝试次数
    await cache_service.reset_login_attempts(credentials.email)

    # 创建令牌
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

    # 创建用户会话缓存
    session_data = {
        "user_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "login_time": datetime.utcnow().isoformat(),
        "access_token": access_token[:20] + "...",  # 只存储token前缀用于标识
    }
    await cache_service.set_user_session(str(user.id), session_data, 86400)  # 24小时

    return ResponseModel(
        data=LoginResponse(
            user=UserRead.from_orm(user),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.post(
    "/send-verification-email",
    response_model=ResponseModel[dict],
    summary="发送验证邮件",
)
async def send_verification_email(
    request: SendVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """发送邮箱验证码"""
    # 检查邮件验证是否启用
    if not settings.EMAIL_VERIFICATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮件验证功能已关闭"
        )

    # 查找用户
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 发送验证邮件
    from ...services.email_verification import email_verification_service

    await email_verification_service.send_verification_email(
        db=db,
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        verification_type="registration",
    )

    return ResponseModel(
        data={"message": "验证邮件已发送", "email": request.email, "expires_in": 1800}
    )


@router.post("/verify-email", response_model=ResponseModel[dict], summary="验证邮箱")
async def verify_email(request: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """验证邮箱"""
    # 检查邮件验证是否启用
    if not settings.EMAIL_VERIFICATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮件验证功能已关闭"
        )

    from ...services.email_verification import email_verification_service

    try:
        if hasattr(request, "verification_token") and request.verification_token:
            # 通过令牌验证
            await email_verification_service.verify_email_by_token(
                db=db,
                verification_token=request.verification_token,
                verification_type="registration",
            )
        elif hasattr(request, "verification_code") and request.verification_code:
            # 通过验证码验证
            await email_verification_service.verify_email_by_code(
                db=db,
                email=request.email,
                verification_code=request.verification_code,
                verification_type="registration",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="请提供验证码或验证令牌"
            )

        return ResponseModel(data={"message": "邮箱验证成功", "email": request.email})

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=ResponseModel[dict], summary="刷新令牌")
async def refresh_token(token: str = Depends(security)):
    """刷新访问令牌"""
    payload = await verify_token(token.credentials)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
        )

    # 创建新的访问令牌
    access_token = create_access_token(
        {"sub": payload["sub"], "email": payload["email"]}
    )

    return ResponseModel(
        data={
            "access_token": access_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


@router.post("/logout", response_model=ResponseModel[dict], summary="用户登出")
async def logout(token: str = Depends(security)):
    """
    用户登出

    - 将当前token加入黑名单
    - 清除用户会话缓存
    """
    from ...core.security import blacklist_token
    from ...services.cache import cache_service

    # 验证token并获取用户信息
    payload = await verify_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的token"
        )

    user_id = payload.get("sub")

    # 将token加入黑名单
    await blacklist_token(token.credentials)

    # 清除用户会话缓存
    if user_id:
        await cache_service.delete_user_session(user_id)

    return ResponseModel(data={"message": "登出成功"})
