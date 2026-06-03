"""
邮件服务工具

支持自建 SMTP 和腾讯云邮件发送
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import random

from src.config import settings


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM
        
        # 腾讯云配置
        self.tencent_secret_id = settings.TENCENT_SECRET_ID
        self.tencent_secret_key = settings.TENCENT_SECRET_KEY
        
        # 判断使用哪种邮件服务
        self.use_tencent = bool(self.tencent_secret_id and self.tencent_secret_key)
        self.use_smtp = bool(self.smtp_host and self.smtp_user)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None
    ) -> tuple:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 纯文本内容
            html_body: HTML 内容（可选）
            
        Returns:
            (success, error_message) 元组
        """
        # 优先使用腾讯云
        if self.use_tencent:
            return await self._send_via_tencent(to_email, subject, body, html_body)
        
        # 其次使用 SMTP
        if self.use_smtp:
            return await self._send_via_smtp(to_email, subject, body, html_body)
        
        # 都没有配置，返回模拟成功（开发环境）
        if settings.DEBUG:
            print(f"[DEBUG] 邮件发送模拟:")
            print(f"  收件人: {to_email}")
            print(f"  主题: {subject}")
            print(f"  内容: {body}")
            return True, None
        
        return False, "邮件服务未配置"
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None
    ) -> tuple:
        """通过 SMTP 发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_from or self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加纯文本
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 添加 HTML（如果有）
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 发送邮件（在线程池中执行）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_smtp_sync,
                to_email,
                msg
            )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _send_smtp_sync(self, to_email: str, msg: MIMEMultipart):
        """同步发送 SMTP 邮件"""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.email_from or self.smtp_user, to_email, msg.as_string())
    
    async def _send_via_tencent(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None
    ) -> tuple:
        """通过腾讯云发送邮件"""
        try:
            # 这里使用腾讯云邮件 API
            # 实际使用时需要安装 tencentcloud-sdk-python
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.ses.v20201002 import ses_client, models
            
            # 创建认证
            cred = credential.Credential(self.tencent_secret_id, self.tencent_secret_key)
            
            # 创建客户端
            httpProfile = HttpProfile()
            httpProfile.endpoint = "ses.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = ses_client.SesClient(cred, "ap-hongkong", clientProfile)
            
            # 构建请求
            req = models.SendEmailRequest()
            req.FromEmailAddress = self.email_from
            req.Destination = [to_email]
            req.Subject = subject
            req.Simple = body
            if html_body:
                req.Html = html_body
            
            # 发送
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, client.SendEmail, req)
            
            return True, None
            
        except ImportError:
            # 未安装腾讯云 SDK，回退到 SMTP 或模拟
            if self.use_smtp:
                return await self._send_via_smtp(to_email, subject, body, html_body)
            if settings.DEBUG:
                print(f"[DEBUG] 腾讯云 SDK 未安装，邮件发送模拟")
                return True, None
            return False, "腾讯云 SDK 未安装"
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """
        生成验证码
        
        Args:
            length: 验证码长度，默认 6 位
            
        Returns:
            数字验证码字符串
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    def create_verification_email(self, code: str, purpose: str = "register") -> tuple:
        """
        创建验证码邮件内容
        
        Args:
            code: 验证码
            purpose: 用途 (register / reset_password)
            
        Returns:
            (subject, body, html_body) 元组
        """
        purpose_text = {
            'register': '注册账号',
            'reset_password': '重置密码'
        }.get(purpose, '验证邮箱')
        
        subject = f"【Prism】您的{purpose_text}验证码"
        
        body = f"""
您好！

您正在进行{purpose_text}操作，验证码为：{code}

验证码有效期为 5 分钟，请尽快使用。

如果这不是您本人的操作，请忽略此邮件。

—— Prism 情报聚合平台
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; text-align: center;">Prism</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; color: #333;">您好！</p>
        <p style="font-size: 16px; color: #333;">您正在进行<strong>{purpose_text}</strong>操作，验证码为：</p>
        <div style="background: white; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px;">{code}</span>
        </div>
        <p style="font-size: 14px; color: #666;">验证码有效期为 <strong>5 分钟</strong>，请尽快使用。</p>
        <p style="font-size: 14px; color: #999;">如果这不是您本人的操作，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #999; text-align: center;">
            —— Prism 情报聚合平台<br>
            让信息更有价值
        </p>
    </div>
</body>
</html>
"""
        
        return subject, body, html_body


# 全局实例
email_service = EmailService()


# 便捷函数
async def send_verification_code(
    to_email: str,
    code: str,
    purpose: str = "register"
) -> tuple:
    """
    发送验证码的便捷函数
    
    Args:
        to_email: 收件人邮箱
        code: 验证码
        purpose: 用途
        
    Returns:
        (success, error_message) 元组
    """
    subject, body, html_body = email_service.create_verification_email(code, purpose)
    return await email_service.send_email(to_email, subject, body, html_body)


def generate_code(length: int = 6) -> str:
    """生成验证码的便捷函数"""
    return EmailService.generate_verification_code(length)