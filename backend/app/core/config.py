"""
核心配置模块 - 支持多环境配置
"""

import os
from typing import List
from enum import Enum


class Environment(str, Enum):
    """环境枚举"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings:
    """应用配置类 - 支持环境特定配置"""

    def __init__(self):
        # 加载环境特定的配置文件
        self._load_environment_config()

        # 应用基础配置
        self.APP_NAME = os.getenv("APP_NAME", "记账App")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
        self.ENVIRONMENT = Environment(os.getenv("ENVIRONMENT", "development"))
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"

        # 服务器配置
        self.SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
        self.SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

        # 数据库配置
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:opennie%40123@lumingcurated.cn:5432/postgres",
        )
        self.DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

        # Redis配置
        self.REDIS_URL = os.getenv(
            "REDIS_URL", "redis://:opennie%40123@47.98.234.55:6379/0"
        )
        self.REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
        self.REDIS_RETRY_ON_TIMEOUT = (
            os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
        )

        # 安全配置
        self.SECRET_KEY = os.getenv(
            "SECRET_KEY", "your-secret-key-change-in-production"
        )
        self.JWT_SECRET_KEY = os.getenv(
            "JWT_SECRET_KEY", "your-jwt-secret-key-change-in-production"
        )
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # CORS配置
        self.CORS_ORIGINS = self._get_list_from_env("CORS_ORIGINS", ["*"])
        self.CORS_ALLOW_CREDENTIALS = (
            os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
        )
        self.ALLOWED_METHODS = self._get_list_from_env("ALLOWED_METHODS", ["*"])
        self.ALLOWED_HEADERS = self._get_list_from_env("ALLOWED_HEADERS", ["*"])

        # 速率限制配置
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

        # 文件上传配置
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.ALLOWED_EXTENSIONS = self._get_list_from_env(
            "ALLOWED_EXTENSIONS", [".jpg", ".jpeg", ".png", ".pdf"]
        )

        # 邮件配置
        self.SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        self.SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.EMAIL_FROM = os.getenv("EMAIL_FROM", self.SMTP_USERNAME)
        self.EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", self.APP_NAME)

        # 邮件验证配置
        self.EMAIL_VERIFICATION_ENABLED = (
            os.getenv("EMAIL_VERIFICATION_ENABLED", "false").lower() == "true"
        )
        self.EMAIL_VERIFICATION_EXPIRE_MINUTES = int(
            os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "30")
        )
        self.EMAIL_SEND_INTERVAL_SECONDS = int(
            os.getenv("EMAIL_SEND_INTERVAL_SECONDS", "60")
        )

        # 前端URL配置
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # 日志配置
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "detailed")

    def _load_environment_config(self):
        """强制加载开发环境配置文件"""
        try:
            from dotenv import load_dotenv

            # 构建配置文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            # 固定使用开发环境配置
            dev_env_file = os.path.join(base_dir, ".env.development")
            if os.path.exists(dev_env_file):
                load_dotenv(dev_env_file, override=True)
                print(f"✅ 强制加载开发环境配置: {dev_env_file}")
            else:
                print(f"❌ 开发环境配置文件不存在: {dev_env_file}")
                # 如果开发配置不存在，尝试加载公用配置作为备用
                common_env_file = os.path.join(base_dir, ".env")
                if os.path.exists(common_env_file):
                    load_dotenv(common_env_file)
                    print(f"⚠️  备用加载公用配置: {common_env_file}")

        except ImportError:
            print("python-dotenv not installed, using environment variables only")

    def _get_list_from_env(self, key: str, default: List[str]) -> List[str]:
        """从环境变量获取列表"""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(",")]
        return default

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT == Environment.STAGING

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT == Environment.TESTING


# 创建全局配置实例
settings = Settings()
