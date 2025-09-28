"""
邮箱验证服务 - 集成Redis缓存
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional
from ..models.email_verification import EmailVerification
from ..models.user import User
from ..core.security import generate_verification_code, generate_verification_token
from ..core.config import settings
from ..core.exceptions import BusinessException
from .email import email_service
from .cache import cache_service
import logging

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """邮箱验证服务类 - 使用Redis缓存优化"""

    async def send_verification_email(
        self,
        db: AsyncSession,
        user_id: str,
        email: str,
        username: Optional[str] = None,
        verification_type: str = "registration",
    ) -> bool:
        """发送验证邮件 - 使用Redis缓存"""

        try:
            # 检查邮件发送限流
            if not await cache_service.can_send_email(
                email, settings.EMAIL_SEND_INTERVAL_SECONDS
            ):
                raise BusinessException(
                    f"请等待 {settings.EMAIL_SEND_INTERVAL_SECONDS} 秒后再发送邮件"
                )

            # 生成验证码和令牌
            verification_code = generate_verification_code()
            verification_token = generate_verification_token()

            # 将验证码存储到Redis缓存中，替代数据库存储
            ttl_seconds = settings.EMAIL_VERIFICATION_EXPIRE_MINUTES * 60
            await cache_service.set_verification_code(
                email=email,
                code=verification_code,
                verification_type=verification_type,
                ttl=ttl_seconds,
            )

            # 同时将验证令牌也缓存起来
            token_key = f"verify_token:{verification_token}"
            token_data = {"email": email, "type": verification_type, "user_id": user_id}
            await cache_service.set_json(token_key, token_data, ttl_seconds)

            # 发送邮件
            if verification_type == "registration":
                success = await email_service.send_verification_email(
                    to_email=email,
                    verification_code=verification_code,
                    verification_token=verification_token,
                    to_name=username,
                )
            elif verification_type == "password_reset":
                success = await email_service.send_password_reset_email(
                    to_email=email,
                    verification_code=verification_code,
                    verification_token=verification_token,
                    to_name=username,
                )
            else:
                raise BusinessException(f"不支持的验证类型: {verification_type}")

            if not success:
                raise BusinessException("邮件发送失败")

            # 标记邮件已发送（用于限流）
            await cache_service.set_email_sent(
                email, settings.EMAIL_SEND_INTERVAL_SECONDS
            )

            logger.info(f"验证邮件发送成功: {email}, 验证码已缓存到Redis")
            return True

        except Exception as e:
            logger.error(f"发送验证邮件失败: {email}, 错误: {str(e)}")
            raise BusinessException(f"发送验证邮件失败: {str(e)}")

    async def verify_email_by_code(
        self,
        db: AsyncSession,
        email: str,
        verification_code: str,
        verification_type: str = "registration",
    ) -> bool:
        """通过验证码验证邮箱 - 使用Redis缓存"""

        try:
            # 从Redis获取验证码数据
            cached_data = await cache_service.get_verification_code(
                email, verification_type
            )

            if not cached_data:
                raise BusinessException("验证码不存在或已过期")

            # 验证验证码
            if cached_data.get("code") != verification_code:
                raise BusinessException("验证码错误")

            # 验证成功，删除缓存的验证码
            await cache_service.delete_verification_code(email, verification_type)

            # 如果是注册验证，更新用户邮箱验证状态
            if verification_type == "registration":
                # 根据邮箱查找用户
                stmt = select(User).where(User.email == email)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.email_verified = True
                    user.email_verified_at = datetime.utcnow()
                    await db.commit()

                    # 清除用户缓存，强制重新加载
                    await cache_service.invalidate_user_cache(str(user.id))

            logger.info(f"邮箱验证成功: {email}, 类型: {verification_type}")
            return True

        except Exception as e:
            logger.error(f"邮箱验证失败: {email}, 错误: {str(e)}")
            raise BusinessException(f"邮箱验证失败: {str(e)}")

    async def verify_email_by_token(
        self,
        db: AsyncSession,
        verification_token: str,
        verification_type: str = "registration",
    ) -> bool:
        """通过令牌验证邮箱 - 使用Redis缓存"""

        try:
            # 从Redis获取令牌数据
            token_key = f"verify_token:{verification_token}"
            token_data = await cache_service.get_json(token_key)

            if not token_data:
                raise BusinessException("验证令牌不存在或已过期")

            # 检查验证类型
            if token_data.get("type") != verification_type:
                raise BusinessException("验证令牌类型不匹配")

            email = token_data.get("email")
            user_id = token_data.get("user_id")

            if not email:
                raise BusinessException("令牌数据异常")

            # 验证成功，删除缓存的令牌和验证码
            await cache_service.delete(token_key)
            await cache_service.delete_verification_code(email, verification_type)

            # 如果是注册验证，更新用户邮箱验证状态
            if verification_type == "registration" and user_id:
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.email_verified = True
                    user.email_verified_at = datetime.utcnow()
                    await db.commit()

                    # 清除用户缓存
                    await cache_service.invalidate_user_cache(str(user.id))

            logger.info(f"邮箱验证成功: {email}, 类型: {verification_type}")
            return True

        except Exception as e:
            logger.error(f"令牌验证失败: {verification_token}, 错误: {str(e)}")
            raise BusinessException(f"令牌验证失败: {str(e)}")

    async def get_verification_status(
        self, email: str, verification_type: str = "registration"
    ) -> dict:
        """获取验证状态"""
        try:
            cached_data = await cache_service.get_verification_code(
                email, verification_type
            )

            if cached_data:
                created_at = cached_data.get("created_at", 0)
                current_time = int(datetime.utcnow().timestamp())
                remaining_time = max(
                    0,
                    settings.EMAIL_VERIFICATION_EXPIRE_MINUTES * 60
                    - (current_time - created_at),
                )

                return {
                    "has_pending_verification": True,
                    "email": email,
                    "type": verification_type,
                    "remaining_seconds": remaining_time,
                }

            return {
                "has_pending_verification": False,
                "email": email,
                "type": verification_type,
            }

        except Exception as e:
            logger.error(f"获取验证状态失败: {email}, 错误: {str(e)}")
            return {"has_pending_verification": False, "error": str(e)}

    async def cleanup_expired_verifications(self, db: AsyncSession) -> int:
        """清理过期的验证记录 - Redis会自动处理过期，这里主要清理数据库"""
        try:
            from sqlalchemy import delete

            stmt = delete(EmailVerification).where(
                EmailVerification.expires_at < datetime.utcnow()
            )
            result = await db.execute(stmt)
            await db.commit()

            deleted_count = result.rowcount
            logger.info(f"清理数据库中过期验证记录: {deleted_count} 条")
            return deleted_count

        except Exception as e:
            logger.error(f"清理过期验证记录失败: {str(e)}")
            return 0

    # 向后兼容的方法（数据库相关）
    async def create_verification(
        self,
        db: AsyncSession,
        user_id: str,
        email: str,
        verification_type: str = "registration",
    ) -> EmailVerification:
        """创建邮箱验证记录（数据库备份）"""
        logger.warning("使用数据库创建验证记录，建议使用Redis缓存版本")

        verification_code = generate_verification_code()
        verification_token = generate_verification_token()

        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        )

        verification = EmailVerification(
            user_id=user_id,
            email=email,
            verification_code=verification_code,
            verification_token=verification_token,
            type=verification_type,
            expires_at=expires_at,
        )

        db.add(verification)
        await db.commit()
        await db.refresh(verification)

        return verification


# 全局邮箱验证服务实例
email_verification_service = EmailVerificationService()
