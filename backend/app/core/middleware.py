"""
全局中间件
"""

import uuid
import time
import logging
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .exceptions import exception_handler, BaseAppException
from ..schemas.common import ErrorResponse, ErrorInfo

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""

    async def dispatch(self, request: Request, call_next):
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 添加到响应头
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # 记录请求开始
        logger.info(
            f"Request started: {request.method} {request.url.path} [{request_id}]"
        )

        try:
            response = await call_next(request)

            # 计算处理时间
            duration = time.time() - start_time

            # 记录请求完成
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} Duration: {duration:.3f}s [{request_id}]"
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Duration: {duration:.3f}s Error: {str(e)} [{request_id}]"
            )
            raise


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except BaseAppException as e:
            # 处理应用自定义异常
            logger.warning(f"Application exception: {e.error_code} - {e.message}")

            error_response = ErrorResponse(
                success=False,
                error=ErrorInfo(
                    code=e.error_code, message=e.message, details=e.details
                ),
                timestamp=datetime.utcnow(),
            )

            # 根据异常类型返回相应的HTTP状态码
            status_code = self._get_status_code_for_exception(e)

            return JSONResponse(status_code=status_code, content=error_response.dict())

        except Exception as e:
            # 处理其他未捕获的异常
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

            error_response = ErrorResponse(
                success=False,
                error=ErrorInfo(
                    code="INTERNAL_ERROR", message="服务器内部错误", details=None
                ),
                timestamp=datetime.utcnow(),
            )

            # 使用dict()方法确保datetime对象正确序列化
            return JSONResponse(status_code=500, content=error_response.dict())

    def _get_status_code_for_exception(self, exception: BaseAppException) -> int:
        """根据异常类型获取HTTP状态码"""
        status_code_map = {
            "VALIDATION_ERROR": 400,
            "AUTHENTICATION_ERROR": 401,
            "AUTHORIZATION_ERROR": 403,
            "ACCOUNT_ACCESS_DENIED": 403,
            "EMAIL_NOT_VERIFIED": 403,
            "RESOURCE_NOT_FOUND": 404,
            "RESOURCE_CONFLICT": 409,
            "BUSINESS_LOGIC_ERROR": 422,
            "INVALID_TRANSACTION": 422,
            "INSUFFICIENT_BALANCE": 422,
            "BUDGET_EXCEEDED": 422,
            "RATE_LIMIT_EXCEEDED": 429,
            "FILE_UPLOAD_ERROR": 400,
            "FILE_FORMAT_ERROR": 400,
            "CURRENCY_CONVERSION_ERROR": 502,
            "EXTERNAL_SERVICE_ERROR": 502,
            "PASSWORD_EXPIRED": 401,
        }

        return status_code_map.get(exception.error_code, 500)


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件（如果需要自定义CORS处理）"""

    def __init__(self, app, allow_origins=None, allow_methods=None, allow_headers=None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 添加CORS头
        if isinstance(self.allow_origins, list):
            origin = request.headers.get("origin")
            if origin in self.allow_origins or "*" in self.allow_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = str(self.allow_origins)

        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
