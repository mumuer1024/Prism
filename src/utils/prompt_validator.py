# -*- coding: utf-8 -*-
"""
Prompt 验证器

验证用户自定义 Prompt 的有效性，包括：
- 长度验证
- 占位符存在性验证
- 未知占位符检测
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import re


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    used_placeholders: List[str] = field(default_factory=list)
    missing_placeholders: List[str] = field(default_factory=list)
    unknown_placeholders: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "used_placeholders": self.used_placeholders,
            "missing_placeholders": self.missing_placeholders,
            "unknown_placeholders": self.unknown_placeholders,
        }


@dataclass
class PlaceholderInfo:
    """占位符信息"""
    placeholder: str
    description: str
    required: bool = False
    example: str = ""

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "placeholder": self.placeholder,
            "description": self.description,
            "required": self.required,
            "example": self.example,
        }


class PromptValidator:
    """
    Prompt 验证器

    验证用户自定义 Prompt 的有效性，确保运行时能正确替换占位符。
    """

    # 各工具支持的占位符
    PLACEHOLDERS: Dict[str, List[str]] = {
        "mission": ["{date_str}", "{time_str}"],
        "bounty_v2ex": [],  # 无占位符
        "alpha": ["{query}"],
        "revenue": ["{content}"],
    }

    # 占位符描述和示例
    PLACEHOLDER_INFO: Dict[str, Dict] = {
        "{date_str}": {
            "description": "日期字符串，运行时替换为当前日期",
            "example": "2026-04-04",
        },
        "{time_str}": {
            "description": "时间字符串，运行时替换为当前时间",
            "example": "10:30:00",
        },
        "{query}": {
            "description": "搜索查询词，Alpha雷达专用，运行时替换为实际搜索词",
            "example": "Solana CLI tools",
        },
        "{content}": {
            "description": "日报内容，营收分析师专用，运行时替换为情报日报全文",
            "example": "（日报内容将在此处插入）",
        },
    }

    # 验证参数
    MIN_LENGTH = 1
    MAX_LENGTH = 50000

    # 占位符正则模式
    PLACEHOLDER_PATTERN = re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}')

    def validate(self, tool_type: str, prompt: str) -> ValidationResult:
        """
        验证 Prompt

        Args:
            tool_type: 工具类型 (mission / bounty_v2ex / alpha / revenue)
            prompt: Prompt 内容

        Returns:
            ValidationResult: 验证结果，包含错误、警告和占位符信息
        """
        errors: List[str] = []
        warnings: List[str] = []
        used: List[str] = []
        missing: List[str] = []
        unknown: List[str] = []

        # 1. 验证工具类型
        if tool_type not in self.PLACEHOLDERS:
            errors.append(f"无效的工具类型: {tool_type}。有效类型: {', '.join(self.PLACEHOLDERS.keys())}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                used_placeholders=used,
                missing_placeholders=missing,
                unknown_placeholders=unknown,
            )

        # 2. 验证长度
        prompt_len = len(prompt)
        if prompt_len < self.MIN_LENGTH:
            errors.append("Prompt 内容不能为空")
        elif prompt_len > self.MAX_LENGTH:
            errors.append(f"Prompt 长度超过限制（当前 {prompt_len} 字符，最大 {self.MAX_LENGTH} 字符）")

        # 3. 提取使用的占位符
        found = self.PLACEHOLDER_PATTERN.findall(prompt)
        used = sorted(set(found))

        # 4. 检查支持的占位符
        supported = set(self.PLACEHOLDERS.get(tool_type, []))
        all_known = set(self.PLACEHOLDER_INFO.keys())

        # 5. 检查缺失的占位符（警告而非错误，因为某些 Prompt 可能不需要）
        for p in supported:
            if p not in used:
                missing.append(p)
                info = self.PLACEHOLDER_INFO.get(p, {})
                desc = info.get("description", "")
                warnings.append(f"建议使用占位符 {p}: {desc}")

        # 6. 检查未知占位符（警告）
        for p in used:
            if p not in all_known:
                unknown.append(p)
                warnings.append(f"未知占位符 {p}，运行时将无法替换，请检查是否拼写错误")

        # 7. 验证结果
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            used_placeholders=used,
            missing_placeholders=missing,
            unknown_placeholders=unknown,
        )

    def get_supported_placeholders(self, tool_type: str) -> List[PlaceholderInfo]:
        """
        获取工具支持的占位符列表

        Args:
            tool_type: 工具类型

        Returns:
            List[PlaceholderInfo]: 占位符信息列表
        """
        if tool_type not in self.PLACEHOLDERS:
            return []

        result: List[PlaceholderInfo] = []
        placeholders = self.PLACEHOLDERS.get(tool_type, [])

        for p in placeholders:
            info = self.PLACEHOLDER_INFO.get(p, {})
            result.append(PlaceholderInfo(
                placeholder=p,
                description=info.get("description", ""),
                required=False,  # 所有占位符都是可选的
                example=info.get("example", ""),
            ))

        return result

    def get_all_placeholders(self) -> Dict[str, List[PlaceholderInfo]]:
        """
        获取所有工具的占位符映射

        Returns:
            Dict[str, List[PlaceholderInfo]]: 工具类型到占位符列表的映射
        """
        result: Dict[str, List[PlaceholderInfo]] = {}
        for tool_type in self.PLACEHOLDERS:
            result[tool_type] = self.get_supported_placeholders(tool_type)
        return result

    def validate_placeholder_syntax(self, placeholder: str) -> bool:
        """
        验证单个占位符语法

        Args:
            placeholder: 占位符字符串

        Returns:
            bool: 是否符合语法
        """
        return bool(self.PLACEHOLDER_PATTERN.fullmatch(placeholder))

    def suggest_placeholders(self, partial: str) -> List[str]:
        """
        根据部分输入建议占位符

        Args:
            partial: 部分占位符输入（如 "{da"）

        Returns:
            List[str]: 匹配的占位符列表
        """
        all_placeholders = list(self.PLACEHOLDER_INFO.keys())

        if not partial:
            return all_placeholders

        # 移除开头的 { 进行匹配
        search = partial.lstrip("{").lower()

        suggestions = []
        for p in all_placeholders:
            name = p.lstrip("{").rstrip("}").lower()
            if name.startswith(search):
                suggestions.append(p)

        return suggestions


def validate_prompt(tool_type: str, prompt: str) -> ValidationResult:
    """
    快捷验证函数

    Args:
        tool_type: 工具类型
        prompt: Prompt 内容

    Returns:
        ValidationResult: 验证结果
    """
    validator = PromptValidator()
    return validator.validate(tool_type, prompt)


def get_placeholders_for_tool(tool_type: str) -> List[Dict]:
    """
    获取工具支持的占位符列表（字典格式）

    Args:
        tool_type: 工具类型

    Returns:
        List[Dict]: 占位符信息列表
    """
    validator = PromptValidator()
    placeholders = validator.get_supported_placeholders(tool_type)
    return [p.to_dict() for p in placeholders]