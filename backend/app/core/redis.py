"""
Redis连接管理
"""

from typing import Optional, Union, Any
import json
import aioredis
from aioredis import Redis
from .config import settings
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis连接管理器"""

    def __init__(self):
        self.redis: Optional[Redis] = None
        self._is_connected = False

    async def connect(self):
        """连接Redis"""
        try:
            # 创建Redis连接
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
                retry_on_timeout=True,
            )

            # 测试连接
            await self.redis.ping()
            self._is_connected = True

            # 获取Redis信息
            info = await self.redis.info()
            redis_version = info.get("redis_version", "unknown")

            logger.info(f"✅ Redis连接成功 (版本: {redis_version})")

        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            # 不抛出异常，允许应用继续运行
            self.redis = None
            self._is_connected = False

    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            self._is_connected = False
            logger.info("✅ Redis连接已关闭")

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self._is_connected or not self.redis:
            return None

        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Union[str, int, float, dict, list],
        expire: Optional[int] = None,
    ) -> bool:
        """设置缓存值"""
        if not self._is_connected or not self.redis:
            return False

        try:
            # 如果值是字典或列表，转为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            result = await self.redis.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._is_connected or not self.redis:
            return False

        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查key是否存在"""
        if not self._is_connected or not self.redis:
            return False

        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置key过期时间"""
        if not self._is_connected or not self.redis:
            return False

        try:
            result = await self.redis.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """增加计数器"""
        if not self._is_connected or not self.redis:
            return None

        try:
            result = await self.redis.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None

    async def get_json(self, key: str) -> Optional[Union[dict, list]]:
        """获取JSON格式的缓存值"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON for key {key}")
        return None

    async def set_json(
        self, key: str, value: Union[dict, list], expire: Optional[int] = None
    ) -> bool:
        """设置JSON格式的缓存值"""
        return await self.set(key, value, expire)

    async def health_check(self) -> dict:
        """Redis健康检查"""
        if not self._is_connected or not self.redis:
            return {"status": "disconnected", "message": "Redis未连接"}

        try:
            # 测试连接
            await self.redis.ping()

            # 获取信息
            info = await self.redis.info()

            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected and self.redis is not None


# 全局Redis管理器实例
redis_manager = RedisManager()
