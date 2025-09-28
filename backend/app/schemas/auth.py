"""
认证数据模式
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from .user import UserRead


class LoginRequest(BaseModel):
    """登录请求"""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""

    username: str
    email: EmailStr
    password: str


class Token(BaseModel):
    """令牌响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """令牌数据"""

    sub: str
    email: str
    type: str


class LoginResponse(BaseModel):
    """登录响应"""

    user: UserRead
    access_token: str
    refresh_token: str
    expires_in: int


class VerifyEmailRequest(BaseModel):
    """邮箱验证请求"""

    email: EmailStr
    verification_code: str


class SendVerificationRequest(BaseModel):
    """发送验证码请求"""

    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""

    token: str
    new_password: str
