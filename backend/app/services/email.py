"""
邮件发送服务
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, BaseLoader
from typing import Optional, List
from ..core.config import settings
from ..core.exceptions import BusinessException
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        content_type: str = "html",
        to_name: Optional[str] = None,
    ) -> bool:
        """发送邮件"""
        try:
            # 创建邮件消息
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = f"{to_name or to_email} <{to_email}>"

            # 添加邮件内容
            part = MIMEText(content, content_type, "utf-8")
            message.attach(part)

            # 连接SMTP服务器并发送
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_use_tls,
            ) as server:
                if self.smtp_username and self.smtp_password:
                    await server.login(self.smtp_username, self.smtp_password)

                await server.send_message(message)

            logger.info(f"邮件发送成功: {to_email}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, 错误: {str(e)}")
            raise BusinessException(f"邮件发送失败: {str(e)}")

    async def send_verification_email(
        self,
        to_email: str,
        verification_code: str,
        verification_token: str,
        to_name: Optional[str] = None,
    ) -> bool:
        """发送邮箱验证邮件"""

        # 构建验证链接
        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        )

        # 邮件模板
        template = Environment(loader=BaseLoader()).from_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮箱验证</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { padding: 40px 30px; }
        .verification-code { background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }
        .code { font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ app_name }}</h1>
            <p>邮箱验证</p>
        </div>

        <div class="content">
            <h2>Hello, {{ to_name or 'User' }}!</h2>
            <p>感谢您注册{{ app_name }}！为了确保账户安全，请验证您的邮箱地址。</p>

            <div class="verification-code">
                <h3>验证码</h3>
                <div class="code">{{ verification_code }}</div>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">请在注册页面输入此验证码</p>
            </div>

            <p>或者点击下方按钮直接验证：</p>
            <p style="text-align: center;">
                <a href="{{ verification_url }}" class="button">验证邮箱</a>
            </p>

            <div class="warning">
                <strong>⚠️ 安全提醒:</strong>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>验证码有效期为 {{ expires_minutes }} 分钟</li>
                    <li>请勿将验证码分享给他人</li>
                    <li>如果您没有注册账户，请忽略此邮件</li>
                </ul>
            </div>

            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
                <code style="background: #f1f3f4; padding: 5px; border-radius: 3px; word-break: break-all;">{{ verification_url }}</code>
            </p>
        </div>

        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复</p>
            <p>&copy; {{ current_year }} {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """)

        # 渲染模板
        html_content = template.render(
            app_name=settings.APP_NAME,
            to_name=to_name,
            verification_code=verification_code,
            verification_url=verification_url,
            expires_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES,
            current_year=2024,
        )

        # 发送邮件
        return await self.send_email(
            to_email=to_email,
            subject=f"{settings.APP_NAME} - 邮箱验证",
            content=html_content,
            content_type="html",
            to_name=to_name,
        )

    async def send_password_reset_email(
        self,
        to_email: str,
        verification_code: str,
        verification_token: str,
        to_name: Optional[str] = None,
    ) -> bool:
        """发送密码重置邮件"""

        # 构建重置链接
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={verification_token}"

        # 简化的密码重置模板
        template = Environment(loader=BaseLoader()).from_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>密码重置</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .code { font-size: 24px; font-weight: bold; color: #e74c3c; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 5px; }
        .button { display: inline-block; background: #e74c3c; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>{{ app_name }} - 密码重置</h2>
        <p>Hello, {{ to_name or 'User' }}!</p>
        <p>您请求重置密码，验证码如下：</p>

        <div class="code">{{ verification_code }}</div>

        <p>或点击链接直接重置: <a href="{{ reset_url }}" class="button">重置密码</a></p>

        <p style="color: #666; font-size: 12px;">验证码有效期 {{ expires_minutes }} 分钟，如非本人操作请忽略此邮件。</p>
    </div>
</body>
</html>
        """)

        html_content = template.render(
            app_name=settings.APP_NAME,
            to_name=to_name,
            verification_code=verification_code,
            reset_url=reset_url,
            expires_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES,
        )

        return await self.send_email(
            to_email=to_email,
            subject=f"{settings.APP_NAME} - 密码重置验证",
            content=html_content,
            content_type="html",
            to_name=to_name,
        )


# 全局邮件服务实例
email_service = EmailService()
