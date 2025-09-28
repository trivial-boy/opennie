"""
异常处理模块 - 使用链式责任模式
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class BaseAppException(Exception):
    """应用基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(BaseAppException):
    """验证错误"""

    def __init__(
        self, message: str = "数据验证失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "VALIDATION_ERROR", details)


class BusinessLogicError(BaseAppException):
    """业务逻辑错误"""

    def __init__(
        self, message: str = "业务逻辑错误", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", details)


class AuthenticationError(BaseAppException):
    """认证错误"""

    def __init__(
        self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(BaseAppException):
    """授权错误"""

    def __init__(
        self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class ResourceNotFoundError(BaseAppException):
    """资源不存在错误"""

    def __init__(
        self, message: str = "资源不存在", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "RESOURCE_NOT_FOUND", details)


class ResourceConflictError(BaseAppException):
    """资源冲突错误"""

    def __init__(
        self, message: str = "资源冲突", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "RESOURCE_CONFLICT", details)


class ExternalServiceError(BaseAppException):
    """外部服务错误"""

    def __init__(
        self, message: str = "外部服务错误", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class RateLimitExceededError(BaseAppException):
    """限流错误"""

    def __init__(
        self, message: str = "请求过于频繁", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


# 记账App业务特定异常
class AccountAccessDeniedError(BaseAppException):
    """账本访问被拒绝错误"""

    def __init__(
        self, message: str = "无权访问该账本", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "ACCOUNT_ACCESS_DENIED", details)


class InsufficientBalanceError(BaseAppException):
    """余额不足错误"""

    def __init__(
        self, message: str = "账户余额不足", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "INSUFFICIENT_BALANCE", details)


class BudgetExceededError(BaseAppException):
    """预算超支错误"""

    def __init__(
        self, message: str = "预算已超支", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "BUDGET_EXCEEDED", details)


class InvalidTransactionError(BaseAppException):
    """无效交易错误"""

    def __init__(
        self, message: str = "无效的交易操作", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "INVALID_TRANSACTION", details)


class FileUploadError(BaseAppException):
    """文件上传错误"""

    def __init__(
        self, message: str = "文件上传失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "FILE_UPLOAD_ERROR", details)


class FileFormatError(BaseAppException):
    """文件格式错误"""

    def __init__(
        self,
        message: str = "不支持的文件格式",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "FILE_FORMAT_ERROR", details)


class CurrencyConversionError(BaseAppException):
    """汇率转换错误"""

    def __init__(
        self, message: str = "汇率转换失败", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "CURRENCY_CONVERSION_ERROR", details)


class EmailNotVerifiedError(BaseAppException):
    """邮箱未验证错误"""

    def __init__(
        self, message: str = "邮箱尚未验证", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "EMAIL_NOT_VERIFIED", details)


class PasswordExpiredError(BaseAppException):
    """密码过期错误"""

    def __init__(
        self,
        message: str = "密码已过期，请重新设置",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "PASSWORD_EXPIRED", details)


# 业务异常别名，向后兼容
BusinessException = BusinessLogicError


# 链式责任模式处理异常
class IExceptionHandler(ABC):
    """异常处理器接口"""

    def __init__(self):
        self._next_handler: Optional["IExceptionHandler"] = None

    def set_next(self, handler: "IExceptionHandler") -> "IExceptionHandler":
        """设置下一个处理器"""
        self._next_handler = handler
        return handler

    @abstractmethod
    def can_handle(self, exception: Exception) -> bool:
        """判断是否能处理该异常"""
        pass

    @abstractmethod
    def handle(self, exception: Exception) -> HTTPException:
        """处理异常"""
        pass

    def process(self, exception: Exception) -> HTTPException:
        """处理异常流程"""
        if self.can_handle(exception):
            return self.handle(exception)
        elif self._next_handler:
            return self._next_handler.process(exception)
        else:
            # 默认处理
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "服务器内部错误",
                        "details": None,
                    },
                },
            )


class ValidationExceptionHandler(IExceptionHandler):
    """验证异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, ValidationError)

    def handle(self, exception: ValidationError) -> HTTPException:
        logger.warning(f"Validation error: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class AuthenticationExceptionHandler(IExceptionHandler):
    """认证异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, AuthenticationError)

    def handle(self, exception: AuthenticationError) -> HTTPException:
        logger.warning(f"Authentication error: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class AuthorizationExceptionHandler(IExceptionHandler):
    """授权异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, AuthorizationError)

    def handle(self, exception: AuthorizationError) -> HTTPException:
        logger.warning(f"Authorization error: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class ResourceNotFoundExceptionHandler(IExceptionHandler):
    """资源不存在异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, ResourceNotFoundError)

    def handle(self, exception: ResourceNotFoundError) -> HTTPException:
        logger.info(f"Resource not found: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class ResourceConflictExceptionHandler(IExceptionHandler):
    """资源冲突异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, ResourceConflictError)

    def handle(self, exception: ResourceConflictError) -> HTTPException:
        logger.warning(f"Resource conflict: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class BusinessLogicExceptionHandler(IExceptionHandler):
    """业务逻辑异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, BusinessLogicError)

    def handle(self, exception: BusinessLogicError) -> HTTPException:
        logger.warning(f"Business logic error: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class RateLimitExceptionHandler(IExceptionHandler):
    """限流异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, RateLimitExceededError)

    def handle(self, exception: RateLimitExceededError) -> HTTPException:
        logger.warning(f"Rate limit exceeded: {exception.message}")
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": exception.error_code,
                    "message": exception.message,
                    "details": exception.details,
                },
            },
        )


class DatabaseExceptionHandler(IExceptionHandler):
    """数据库异常处理器"""

    def can_handle(self, exception: Exception) -> bool:
        # 检查是否是SQLAlchemy异常
        return (
            "sqlalchemy" in str(type(exception)).lower()
            or "database" in str(exception).lower()
            or "connection" in str(exception).lower()
        )

    def handle(self, exception: Exception) -> HTTPException:
        error_msg = str(exception).lower()

        if "duplicate key" in error_msg or "unique constraint" in error_msg:
            logger.warning(f"Database duplicate key error: {exception}")
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "error": {
                        "code": "DUPLICATE_RESOURCE",
                        "message": "资源已存在",
                        "details": None,
                    },
                },
            )
        elif "foreign key" in error_msg:
            logger.warning(f"Database foreign key error: {exception}")
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_REFERENCE",
                        "message": "关联资源不存在",
                        "details": None,
                    },
                },
            )
        else:
            logger.error(f"Database error: {exception}")
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": {
                        "code": "DATABASE_ERROR",
                        "message": "数据库操作失败",
                        "details": None,
                    },
                },
            )


class ExceptionHandlerChain:
    """异常处理链"""

    def __init__(self):
        # 构建处理链
        self.handler_chain = self._build_chain()

    def _build_chain(self) -> IExceptionHandler:
        """构建异常处理链"""
        # 创建处理器
        validation_handler = ValidationExceptionHandler()
        auth_handler = AuthenticationExceptionHandler()
        authz_handler = AuthorizationExceptionHandler()
        not_found_handler = ResourceNotFoundExceptionHandler()
        conflict_handler = ResourceConflictExceptionHandler()
        business_handler = BusinessLogicExceptionHandler()
        rate_limit_handler = RateLimitExceptionHandler()
        database_handler = DatabaseExceptionHandler()

        # 构建处理链
        validation_handler.set_next(auth_handler).set_next(authz_handler).set_next(
            not_found_handler
        ).set_next(conflict_handler).set_next(business_handler).set_next(
            rate_limit_handler
        ).set_next(database_handler)

        return validation_handler

    def handle_exception(self, exception: Exception) -> HTTPException:
        """处理异常"""
        return self.handler_chain.process(exception)


# 全局异常处理器实例
exception_handler = ExceptionHandlerChain()
