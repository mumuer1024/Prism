"""
密码加密处理工具

提供密码哈希加密和验证功能
使用 bcrypt 算法
"""

import bcrypt
from typing import Optional
import re
import secrets
import string

from src.config import settings


class PasswordHandler:
    """密码处理类"""

    def __init__(self, rounds: int = 12):
        """
        初始化密码处理器

        Args:
            rounds: bcrypt 加密轮数，默认 12
        """
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """
        对密码进行哈希加密

        Args:
            password: 明文密码

        Returns:
            哈希后的密码字符串

        Note:
            bcrypt 有 72 字节的密码长度限制，超过部分会被截断
        """
        # bcrypt 限制密码长度为 72 字节，先截断
        password_bytes = password.encode('utf-8')[:72]
        # 生成盐并哈希
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确

        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码

        Returns:
            验证结果 True/False

        Note:
            bcrypt 有 72 字节的密码长度限制，超过部分会被截断
        """
        # bcrypt 限制密码长度为 72 字节，先截断
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    def needs_update(self, hashed_password: str) -> bool:
        """
        检查密码哈希是否需要更新（如轮数变化）

        Args:
            hashed_password: 哈希后的密码

        Returns:
            是否需要更新
        """
        try:
            # 提取当前轮数
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < self.rounds
        except Exception:
            pass
        return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple:
        """
        验证密码强度

        要求：
        - 至少 8 个字符
        - 包含至少一个字母
        - 包含至少一个数字

        Args:
            password: 待验证的密码

        Returns:
            (is_valid, error_message) 元组
        """
        if len(password) < 8:
            return False, "密码长度至少需要 8 个字符"

        if not re.search(r'[a-zA-Z]', password):
            return False, "密码需要包含至少一个字母"

        if not re.search(r'[0-9]', password):
            return False, "密码需要包含至少一个数字"

        # 可选：检查常见弱密码
        weak_passwords = [
            'password', 'password1', 'password123', '12345678',
            'qwerty123', 'abc12345', 'admin123', 'user1234'
        ]
        if password.lower() in weak_passwords:
            return False, "密码过于简单，请使用更强的密码"

        return True, ""

    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """
        生成随机密码

        Args:
            length: 密码长度，默认 16

        Returns:
            随机生成的密码
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))

        # 确保包含至少一个字母和一个数字
        if not re.search(r'[a-zA-Z]', password):
            password = secrets.choice(string.ascii_letters) + password[1:]
        if not re.search(r'[0-9]', password):
            password = password[:-1] + secrets.choice(string.digits)

        return password


# 全局实例
password_handler = PasswordHandler()


# 便捷函数
def hash_password(password: str) -> str:
    """哈希密码的便捷函数"""
    return password_handler.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码的便捷函数"""
    return password_handler.verify_password(plain_password, hashed_password)


def validate_password(password: str) -> tuple:
    """
    验证密码强度的便捷函数

    Returns:
        (is_valid, error_message) 元组
    """
    return PasswordHandler.validate_password_strength(password)


# 别名，保持向后兼容
validate_password_strength = validate_password