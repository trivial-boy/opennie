"""
记账App后端主应用 - 使用设计模式重构
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

from .core.config import settings
from .core.database import init_database, close_database, db
from .core.redis import redis_manager
from .core.exceptions import exception_handler, BaseAppException
from .core.container import ContainerBuilder, set_container
from .api.v1 import api_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ApplicationFactory:
    """应用工厂类"""

    @staticmethod
    def create_app() -> FastAPI:
        """创建FastAPI应用"""
        return FastAPI(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="现代化的个人财务管理API，使用优雅的设计模式构建",
            docs_url="/docs" if settings.is_development else None,
            redoc_url="/redoc" if settings.is_development else None,
            lifespan=ApplicationLifecycle.get_lifespan,
        )

    @staticmethod
    def configure_middleware(app: FastAPI):
        """配置中间件"""
        from .core.middleware import (
            RequestIDMiddleware,
            LoggingMiddleware,
            ExceptionHandlingMiddleware,
            SecurityHeadersMiddleware,
        )

        # 添加自定义中间件（按执行顺序添加）
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(ExceptionHandlingMiddleware)
        app.add_middleware(LoggingMiddleware)
        app.add_middleware(RequestIDMiddleware)

        # CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.ALLOWED_METHODS,
            allow_headers=settings.ALLOWED_HEADERS,
        )

    @staticmethod
    def configure_exception_handlers(app: FastAPI):
        """配置异常处理器"""

        @app.exception_handler(BaseAppException)
        async def app_exception_handler(request: Request, exc: BaseAppException):
            """应用异常处理"""
            http_exception = exception_handler.handle_exception(exc)
            return JSONResponse(
                status_code=http_exception.status_code, content=http_exception.detail
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """通用异常处理"""
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            http_exception = exception_handler.handle_exception(exc)
            return JSONResponse(
                status_code=http_exception.status_code, content=http_exception.detail
            )

    @staticmethod
    def register_routes(app: FastAPI):
        """注册路由"""

        # 健康检查路由
        @app.get("/", tags=["健康检查"])
        async def root():
            """根路径 - 服务健康检查"""
            return {
                "message": "🎉 记账App后端服务运行正常",
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT.value,
                "docs_url": "/docs" if settings.is_development else "disabled",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.get("/health", tags=["健康检查"])
        async def health_check():
            """详细健康检查"""
            try:
                # 检查数据库连接
                db_health = await db.check_health()

                # 检查Redis连接
                redis_status = "connected" if redis_manager.redis else "disconnected"

                return {
                    "status": "healthy",
                    "services": {"database": db_health, "redis": redis_status},
                    "environment": settings.ENVIRONMENT.value,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        # 注册API路由
        app.include_router(api_router, prefix="/api/v1")


class DependencyInjectionSetup:
    """依赖注入设置"""

    @staticmethod
    def configure_container():
        """配置依赖注入容器"""
        builder = ContainerBuilder()

        # 注册核心服务
        from .core.redis import RedisManager

        builder.add_singleton(RedisManager, RedisManager)

        # 注册Repository
        from .repositories.user import UserRepository

        builder.add_scoped(UserRepository, UserRepository)

        # 注册Service
        from .services.user import UserService

        builder.add_scoped(UserService, UserService)

        # 构建并设置容器
        container = builder.build()
        set_container(container)

        logger.info("✅ 依赖注入容器配置完成")


class ApplicationLifecycle:
    """应用生命周期管理"""

    @staticmethod
    @asynccontextmanager
    async def get_lifespan(app: FastAPI):
        """获取应用生命周期上下文管理器"""
        # 启动时
        await ApplicationLifecycle.startup()
        yield
        # 关闭时
        await ApplicationLifecycle.shutdown()

    @staticmethod
    async def startup():
        """应用启动"""
        logger.info("🚀 启动记账App后端服务...")

        try:
            # 配置依赖注入
            DependencyInjectionSetup.configure_container()

            # 初始化数据库
            await init_database()
            logger.info("✅ 数据库连接成功")

            # 连接Redis
            await redis_manager.connect()
            logger.info("✅ Redis连接成功")

            logger.info(f"🎉 记账App后端服务启动成功！")
            logger.info(f"📍 环境: {settings.ENVIRONMENT.value}")
            logger.info(f"🌐 访问地址: http://localhost:8000")
            if settings.is_development:
                logger.info(f"📚 API文档: http://localhost:8000/docs")

        except Exception as e:
            logger.error(f"❌ 应用启动失败: {e}")
            raise

    @staticmethod
    async def shutdown():
        """应用关闭"""
        logger.info("⏹️  正在关闭记账App后端服务...")

        try:
            # 关闭Redis连接
            await redis_manager.disconnect()
            logger.info("✅ Redis连接已关闭")

            # 关闭数据库连接
            await close_database()
            logger.info("✅ 数据库连接已关闭")

            logger.info("👋 记账App后端服务已安全关闭")

        except Exception as e:
            logger.error(f"❌ 应用关闭时出错: {e}")


def create_application() -> FastAPI:
    """创建应用实例 - 工厂方法"""
    # 创建应用
    app = ApplicationFactory.create_app()

    # 配置中间件
    ApplicationFactory.configure_middleware(app)

    # 配置异常处理
    ApplicationFactory.configure_exception_handlers(app)

    # 注册路由
    ApplicationFactory.register_routes(app)

    return app


# 创建应用实例
app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
