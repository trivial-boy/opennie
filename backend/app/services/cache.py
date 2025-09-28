"""
Redis缓存服务 - 基于现有redis_manager
"""

from typing import Optional, Any, Dict, List, Union
import json
import logging
from datetime import datetime, timedelta
from ..core.redis import redis_manager
from ..core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis缓存服务类"""

    def __init__(self):
        self.redis = redis_manager
        self.default_ttl = 3600  # 默认1小时过期

    # 基础缓存操作
    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        return await self.redis.get(key)

    async def set(
        self,
        key: str,
        value: Union[str, dict, list, int, float],
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存值"""
        expire = ttl or self.default_ttl
        return await self.redis.set(key, value, expire)

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """检查key是否存在"""
        return await self.redis.exists(key)

    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        return await self.redis.expire(key, ttl)

    async def get_json(self, key: str) -> Optional[Union[dict, list]]:
        """获取JSON格式的缓存值"""
        return await self.redis.get_json(key)

    async def set_json(
        self, key: str, value: Union[dict, list], ttl: Optional[int] = None
    ) -> bool:
        """设置JSON格式的缓存值"""
        expire = ttl or self.default_ttl
        return await self.redis.set_json(key, value, expire)

    # 用户会话缓存
    async def set_user_session(
        self, user_id: str, session_data: dict, ttl: int = 86400
    ) -> bool:
        """设置用户会话缓存 (默认24小时)"""
        key = f"user:session:{user_id}"
        return await self.set_json(key, session_data, ttl)

    async def get_user_session(self, user_id: str) -> Optional[dict]:
        """获取用户会话缓存"""
        key = f"user:session:{user_id}"
        return await self.get_json(key)

    async def delete_user_session(self, user_id: str) -> bool:
        """删除用户会话缓存"""
        key = f"user:session:{user_id}"
        return await self.delete(key)

    # JWT Token黑名单
    async def blacklist_token(self, token: str, ttl: int) -> bool:
        """将token加入黑名单"""
        key = f"blacklist:token:{token}"
        return await self.set(key, "blacklisted", ttl)

    async def is_token_blacklisted(self, token: str) -> bool:
        """检查token是否在黑名单"""
        key = f"blacklist:token:{token}"
        return await self.exists(key)

    # 邮箱验证码缓存
    async def set_verification_code(
        self,
        email: str,
        code: str,
        verification_type: str = "registration",
        ttl: int = 1800,  # 30分钟
    ) -> bool:
        """设置邮箱验证码"""
        key = f"verify:{verification_type}:{email}"
        data = {
            "code": code,
            "email": email,
            "type": verification_type,
            "created_at": int(datetime.utcnow().timestamp()),
        }
        return await self.set_json(key, data, ttl)

    async def get_verification_code(
        self, email: str, verification_type: str = "registration"
    ) -> Optional[dict]:
        """获取邮箱验证码"""
        key = f"verify:{verification_type}:{email}"
        return await self.get_json(key)

    async def delete_verification_code(
        self, email: str, verification_type: str = "registration"
    ) -> bool:
        """删除邮箱验证码"""
        key = f"verify:{verification_type}:{email}"
        return await self.delete(key)

    # API限流缓存
    async def increment_request_count(
        self, identifier: str, window_seconds: int = 60
    ) -> int:
        """增加请求计数"""
        key = f"rate_limit:{identifier}"
        try:
            # 使用Redis的原子操作
            current = await self.redis.incr(key)
            if current == 1:
                # 第一次请求，设置过期时间
                await self.redis.expire(key, window_seconds)
            return current
        except Exception as e:
            logger.error(f"Redis increment error: {key}, {str(e)}")
            return 0

    async def get_request_count(self, identifier: str) -> int:
        """获取请求计数"""
        key = f"rate_limit:{identifier}"
        try:
            count = await self.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Redis get count error: {key}, {str(e)}")
            return 0

    async def reset_request_count(self, identifier: str) -> bool:
        """重置请求计数"""
        key = f"rate_limit:{identifier}"
        return await self.delete(key)

    # 邮件发送限流
    async def can_send_email(self, email: str, interval_seconds: int = 60) -> bool:
        """检查是否可以发送邮件"""
        key = f"email_limit:{email}"
        return not await self.exists(key)

    async def set_email_sent(self, email: str, interval_seconds: int = 60) -> bool:
        """标记邮件已发送"""
        key = f"email_limit:{email}"
        return await self.set(key, "sent", interval_seconds)

    # 用户信息缓存
    async def cache_user_info(
        self, user_id: str, user_data: dict, ttl: int = 3600
    ) -> bool:
        """缓存用户信息 (默认1小时)"""
        key = f"user:info:{user_id}"
        # 移除敏感信息
        safe_data = {
            k: v for k, v in user_data.items() if k not in ["password_hash", "password"]
        }
        return await self.set_json(key, safe_data, ttl)

    async def get_cached_user_info(self, user_id: str) -> Optional[dict]:
        """获取缓存的用户信息"""
        key = f"user:info:{user_id}"
        return await self.get_json(key)

    async def invalidate_user_cache(self, user_id: str) -> bool:
        """使用户缓存失效"""
        keys = [f"user:info:{user_id}", f"user:session:{user_id}"]

        success = True
        for key in keys:
            if not await self.delete(key):
                success = False

        return success

    # 登录尝试限制
    async def increment_login_attempts(
        self, identifier: str, window_seconds: int = 900
    ) -> int:
        """增加登录尝试次数 (默认15分钟窗口)"""
        key = f"login_attempts:{identifier}"
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window_seconds)
            return current
        except Exception as e:
            logger.error(f"Redis login attempts error: {key}, {str(e)}")
            return 0

    async def get_login_attempts(self, identifier: str) -> int:
        """获取登录尝试次数"""
        key = f"login_attempts:{identifier}"
        try:
            count = await self.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Redis get login attempts error: {key}, {str(e)}")
            return 0

    async def reset_login_attempts(self, identifier: str) -> bool:
        """重置登录尝试次数"""
        key = f"login_attempts:{identifier}"
        return await self.delete(key)

    # 健康检查
    async def health_check(self) -> dict:
        """Redis健康检查"""
        return await self.redis.health_check()

    # 缓存统计
    async def get_cache_info(self) -> dict:
        """获取缓存信息"""
        health = await self.health_check()
        return {
            "redis_status": health.get("status"),
            "redis_version": health.get("redis_version"),
            "connected_clients": health.get("connected_clients"),
            "used_memory": health.get("used_memory_human"),
            "uptime": health.get("uptime_in_seconds"),
        }


# 全局缓存服务实例
cache_service = CacheService()
