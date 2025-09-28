"""
安全相关工具：JWT、密码哈希等
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from passlib.context import CryptContext
from .config import settings


# 密码哈希上下文 - 临时使用pbkdf2_sha256来避免bcrypt版本问题
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证令牌"""
    try:
        # 检查token是否在黑名单中
        from ..services.cache import cache_service

        if await cache_service.is_token_blacklisted(token):
            return None

        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def blacklist_token(token: str) -> bool:
    """将token加入黑名单"""
    try:
        # 解析token获取过期时间
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        from datetime import datetime

        exp = payload.get("exp")
        if exp:
            # 计算剩余过期时间
            ttl = max(0, exp - int(datetime.utcnow().timestamp()))

            from ..services.cache import cache_service

            return await cache_service.blacklist_token(token, ttl)

        return False
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # bcrypt有72字节限制，需要正确截断UTF-8编码的字节
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        # 确保截断不会破坏UTF-8字符
        password_bytes = password_bytes[:72]
        # 解码回字符串，忽略不完整的字符
        password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # bcrypt有72字节限制，需要正确截断UTF-8编码的字节
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        # 确保截断不会破坏UTF-8字符
        password_bytes = password_bytes[:72]
        # 解码回字符串，忽略不完整的字符
        plain_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(plain_password, hashed_password)


def generate_verification_code() -> str:
    """生成6位验证码"""
    import random

    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def generate_verification_token() -> str:
    """生成验证令牌"""
    import secrets

    return secrets.token_urlsafe(32)
