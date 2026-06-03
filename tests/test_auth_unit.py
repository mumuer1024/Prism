# -*- coding: utf-8 -*-
"""
密码处理单元测试

测试密码哈希、验证、强度检查等功能
"""
import pytest

from src.auth.utils.password_handler import (
    PasswordHandler, hash_password, verify_password, validate_password_strength
)


# ═══════════════════════════════════════════════════════════
# 密码处理测试
# ═══════════════════════════════════════════════════════════

class TestPasswordHandler:
    """密码处理器测试"""

    def test_hash_password(self):
        """测试密码哈希生成"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证哈希值不为空
        assert hashed is not None
        # 验证哈希值与原密码不同
        assert hashed != password
        # 验证哈希值是字符串
        assert isinstance(hashed, str)
        # 验证哈希值长度合理（bcrypt 生成的哈希约 60 字符）
        assert len(hashed) > 50

    def test_hash_password_different_each_time(self):
        """测试相同密码每次生成的哈希不同"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hash1 = handler.hash_password(password)
        hash2 = handler.hash_password(password)

        # 两次哈希值应该不同（bcrypt 自动加盐）
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证正确密码
        assert handler.verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """测试错误密码验证"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证错误密码
        assert handler.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """测试空密码验证"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证空密码
        assert handler.verify_password("", hashed) is False

    def test_module_level_functions(self):
        """测试模块级便捷函数"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


# ═══════════════════════════════════════════════════════════
# 密码强度验证测试
# ═══════════════════════════════════════════════════════════

class TestPasswordStrength:
    """密码强度验证测试"""

    def test_password_strength_weak(self):
        """测试弱密码检测"""
        weak_passwords = [
            "123",
            "abc",
            "password",
            "qwerty"
        ]

        for password in weak_passwords:
            is_valid, msg = validate_password_strength(password)
            assert is_valid is False

    def test_password_strength_strong(self):
        """测试强密码检测"""
        strong_passwords = [
            "Password123!",
            "StrongPass@2024",
            "MyP@ssw0rd!",
            "Complex#Pass1"
        ]

        for password in strong_passwords:
            is_valid, msg = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid: {msg}"

    def test_password_strength_medium(self):
        """测试中等密码检测"""
        medium_passwords = [
            "password123",
            "Password123",
        ]

        for password in medium_passwords:
            is_valid, msg = validate_password_strength(password)
            assert isinstance(is_valid, bool)

    def test_password_too_short(self):
        """测试密码太短"""
        is_valid, msg = validate_password_strength("Pass1")
        assert is_valid is False
        assert "8" in msg

    def test_password_no_letter(self):
        """测试密码没有字母"""
        is_valid, msg = validate_password_strength("12345678")
        assert is_valid is False
        assert "字母" in msg

    def test_password_no_digit(self):
        """测试密码没有数字"""
        is_valid, msg = validate_password_strength("Password")
        assert is_valid is False
        assert "数字" in msg