"""
装饰器模块 - 使用装饰器模式
"""

from functools import wraps
from typing import Callable, Any, Dict, Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import time
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class RateLimiter(ABC):
    """限流器抽象基类"""

    @abstractmethod
    async def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        pass


class MemoryRateLimiter(RateLimiter):
    """内存限流器实现"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}

    async def is_allowed(self, key: str) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_seconds

        if key not in self.requests:
            self.requests[key] = []

        # 清理过期请求
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > window_start
        ]

        # 检查是否超过限制
        if len(self.requests[key]) >= self.max_requests:
            return False

        # 记录当前请求
        self.requests[key].append(current_time)
        return True


class RedisRateLimiter(RateLimiter):
    """Redis限流器实现"""

    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        # Redis滑动窗口限流实现
        current_time = time.time()
        window_start = current_time - self.window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, self.window_seconds)

        results = await pipe.execute()
        request_count = results[1]

        return request_count < self.max_requests


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """限流装饰器"""
    limiter = MemoryRateLimiter(max_requests, window_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求中获取客户端IP
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request:
                client_ip = request.client.host
                key = f"rate_limit:{client_ip}"

                if not await limiter.is_allowed(key):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="请求过于频繁，请稍后再试",
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def log_performance(func: Callable) -> Callable:
    """性能日志装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} executed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise

    return wrapper


def handle_db_errors(func: Callable) -> Callable:
    """数据库错误处理装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")

            # 根据不同错误类型返回不同响应
            if "duplicate key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="资源已存在"
                )
            elif "foreign key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="关联资源不存在"
                )
            elif "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="服务器内部错误",
                )

    return wrapper


def validate_permissions(required_permissions: list = None):
    """权限验证装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里可以添加权限验证逻辑
            # 暂时直接通过
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl_seconds: int = 300, key_prefix: str = "cache"):
    """结果缓存装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 这里可以添加Redis缓存逻辑
            # 暂时直接执行函数
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class APIDecorators:
    """API装饰器集合"""

    @staticmethod
    def standard_api(max_requests: int = 100):
        """标准API装饰器组合"""

        def decorator(func: Callable) -> Callable:
            # 组合多个装饰器
            func = log_performance(func)
            func = handle_db_errors(func)
            func = rate_limit(max_requests)(func)
            return func

        return decorator

    @staticmethod
    def public_api():
        """公共API装饰器（无需认证）"""

        def decorator(func: Callable) -> Callable:
            func = log_performance(func)
            func = rate_limit(200)(func)  # 更宽松的限流
            return func

        return decorator

    @staticmethod
    def admin_api():
        """管理员API装饰器"""

        def decorator(func: Callable) -> Callable:
            func = log_performance(func)
            func = handle_db_errors(func)
            func = validate_permissions(["admin"])(func)
            func = rate_limit(50)(func)  # 更严格的限流
            return func

        return decorator
