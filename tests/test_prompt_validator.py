# -*- coding: utf-8 -*-
"""
Prompt 验证器测试

测试 PromptValidator 的核心功能：
- 长度验证
- 占位符验证
- 未知占位符检测
- API 端点测试
"""

import pytest
from src.utils.prompt_validator import (
    PromptValidator,
    ValidationResult,
    PlaceholderInfo,
    validate_prompt,
    get_placeholders_for_tool,
)


class TestPromptValidatorCore:
    """验证器核心功能测试"""

    @pytest.fixture
    def validator(self):
        return PromptValidator()

    def test_valid_prompt(self, validator):
        """测试有效的 Prompt"""
        result = validator.validate("mission", "这是一个测试 Prompt，日期: {date_str}")

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "{date_str}" in result.used_placeholders

    def test_valid_prompt_with_multiple_placeholders(self, validator):
        """测试包含多个占位符的有效 Prompt"""
        result = validator.validate("mission", "日期: {date_str}, 时间: {time_str}")

        assert result.is_valid is True
        assert "{date_str}" in result.used_placeholders
        assert "{time_str}" in result.used_placeholders

    def test_valid_prompt_no_placeholders(self, validator):
        """测试无占位符的有效 Prompt"""
        result = validator.validate("bounty_v2ex", "这是一个没有占位符的 Prompt")

        assert result.is_valid is True
        assert len(result.used_placeholders) == 0

    def test_empty_prompt(self, validator):
        """测试空 Prompt"""
        result = validator.validate("mission", "")

        assert result.is_valid is False
        assert "不能为空" in result.errors[0]

    def test_whitespace_only_prompt(self, validator):
        """测试仅包含空白字符的 Prompt"""
        result = validator.validate("mission", "   ")

        # 空白字符长度为 3，所以是有效的（只是有警告）
        assert result.is_valid is True
        assert len(result.warnings) > 0  # 缺失占位符警告

    def test_too_long_prompt(self, validator):
        """测试超长 Prompt"""
        long_content = "x" * 60000
        result = validator.validate("mission", long_content)

        assert result.is_valid is False
        assert "超过限制" in result.errors[0]

    def test_invalid_tool_type(self, validator):
        """测试无效工具类型"""
        result = validator.validate("invalid_type", "测试内容")

        assert result.is_valid is False
        assert "无效的工具类型" in result.errors[0]

    def test_result_to_dict(self, validator):
        """测试结果转换为字典"""
        result = validator.validate("mission", "{date_str}")
        dict_result = result.to_dict()

        assert "is_valid" in dict_result
        assert "errors" in dict_result
        assert "warnings" in dict_result
        assert "used_placeholders" in dict_result
        assert dict_result["is_valid"] is True


class TestPlaceholderValidation:
    """占位符验证测试"""

    @pytest.fixture
    def validator(self):
        return PromptValidator()

    def test_used_placeholders_detected(self, validator):
        """测试已使用占位符检测"""
        result = validator.validate("alpha", "搜索: {query}")

        assert "{query}" in result.used_placeholders

    def test_multiple_used_placeholders(self, validator):
        """测试多个已使用占位符"""
        result = validator.validate("mission", "{date_str} {time_str} {date_str}")

        # 重复的占位符应该只出现一次
        assert result.used_placeholders == ["{date_str}", "{time_str}"]

    def test_missing_placeholders_warning(self, validator):
        """测试缺失占位符警告"""
        result = validator.validate("mission", "没有占位符的 Prompt")

        assert result.is_valid is True  # 缺失是警告，不是错误
        assert "{date_str}" in result.missing_placeholders
        assert "{time_str}" in result.missing_placeholders
        assert len(result.warnings) > 0

    def test_unknown_placeholders_warning(self, validator):
        """测试未知占位符警告"""
        result = validator.validate("mission", "使用未知占位符: {unknown_var}")

        assert result.is_valid is True  # 未知占位符是警告
        assert "{unknown_var}" in result.unknown_placeholders
        # 检查警告中是否包含未知占位符警告（可能在多个警告中）
        has_unknown_warning = any("未知占位符" in w for w in result.warnings)
        assert has_unknown_warning

    def test_no_placeholders_required_for_bounty(self, validator):
        """测试无占位符工具（bounty_v2ex）"""
        result = validator.validate("bounty_v2ex", "筛选规则")

        assert result.is_valid is True
        assert len(result.missing_placeholders) == 0
        assert len(result.used_placeholders) == 0

    def test_no_placeholders_required_for_chrome(self, validator):
        """测试无占位符工具（bounty_chrome）"""
        result = validator.validate("bounty_chrome", "扩展筛选")

        assert result.is_valid is True
        assert len(result.missing_placeholders) == 0

    def test_alpha_query_placeholder(self, validator):
        """测试 Alpha 雷达的 query 占位符"""
        result = validator.validate("alpha", "搜索 {query} 相关项目")

        assert "{query}" in result.used_placeholders
        assert len(result.missing_placeholders) == 0

    def test_revenue_content_placeholder(self, validator):
        """测试营收分析师的 content 占位符"""
        result = validator.validate("revenue", "分析内容: {content}")

        assert "{content}" in result.used_placeholders


class TestPlaceholderSyntax:
    """占位符语法测试"""

    @pytest.fixture
    def validator(self):
        return PromptValidator()

    def test_valid_placeholder_syntax(self, validator):
        """测试有效的占位符语法"""
        assert validator.validate_placeholder_syntax("{date_str}") is True
        assert validator.validate_placeholder_syntax("{query}") is True
        assert validator.validate_placeholder_syntax("{content}") is True

    def test_invalid_placeholder_syntax(self, validator):
        """测试无效的占位符语法"""
        assert validator.validate_placeholder_syntax("date_str") is False
        assert validator.validate_placeholder_syntax("{123}") is False
        # {_} 是有效的，因为 _ 是允许的起始字符
        assert validator.validate_placeholder_syntax("{_}") is True
        assert validator.validate_placeholder_syntax("{}") is False
        assert validator.validate_placeholder_syntax("{1abc}") is False

    def test_placeholder_with_numbers(self, validator):
        """测试包含数字的占位符"""
        assert validator.validate_placeholder_syntax("{var_123}") is True

    def test_placeholder_with_underscore(self, validator):
        """测试包含下划线的占位符"""
        assert validator.validate_placeholder_syntax("{my_var_name}") is True


class TestPlaceholderSuggestions:
    """占位符建议测试"""

    @pytest.fixture
    def validator(self):
        return PromptValidator()

    def test_suggest_all_placeholders(self, validator):
        """测试建议所有占位符"""
        suggestions = validator.suggest_placeholders("")
        assert len(suggestions) == 4  # 所有已知占位符

    def test_suggest_by_partial_match(self, validator):
        """测试部分匹配建议"""
        suggestions = validator.suggest_placeholders("{da")
        assert "{date_str}" in suggestions

    def test_suggest_by_query_partial(self, validator):
        """测试 query 部分匹配"""
        suggestions = validator.suggest_placeholders("{qu")
        assert "{query}" in suggestions

    def test_no_suggestions_for_invalid_partial(self, validator):
        """测试无效部分无建议"""
        suggestions = validator.suggest_placeholders("{xyz")
        assert len(suggestions) == 0


class TestGetPlaceholders:
    """获取占位符测试"""

    @pytest.fixture
    def validator(self):
        return PromptValidator()

    def test_get_mission_placeholders(self, validator):
        """测试获取 mission 占位符"""
        placeholders = validator.get_supported_placeholders("mission")

        assert len(placeholders) == 2
        assert any(p.placeholder == "{date_str}" for p in placeholders)
        assert any(p.placeholder == "{time_str}" for p in placeholders)

    def test_get_alpha_placeholders(self, validator):
        """测试获取 alpha 占位符"""
        placeholders = validator.get_supported_placeholders("alpha")

        assert len(placeholders) == 1
        assert placeholders[0].placeholder == "{query}"

    def test_get_revenue_placeholders(self, validator):
        """测试获取 revenue 占位符"""
        placeholders = validator.get_supported_placeholders("revenue")

        assert len(placeholders) == 1
        assert placeholders[0].placeholder == "{content}"

    def test_get_bounty_placeholders_empty(self, validator):
        """测试获取 bounty 占位符（应为空）"""
        placeholders_v2ex = validator.get_supported_placeholders("bounty_v2ex")
        placeholders_chrome = validator.get_supported_placeholders("bounty_chrome")

        assert len(placeholders_v2ex) == 0
        assert len(placeholders_chrome) == 0

    def test_get_invalid_tool_placeholders(self, validator):
        """测试无效工具类型返回空列表"""
        placeholders = validator.get_supported_placeholders("invalid")
        assert len(placeholders) == 0

    def test_get_all_placeholders(self, validator):
        """测试获取所有工具的占位符"""
        all_placeholders = validator.get_all_placeholders()

        assert "mission" in all_placeholders
        assert "alpha" in all_placeholders
        assert "revenue" in all_placeholders
        assert "bounty_v2ex" in all_placeholders
        assert "bounty_chrome" in all_placeholders

    def test_placeholder_info_to_dict(self, validator):
        """测试 PlaceholderInfo 转换为字典"""
        placeholders = validator.get_supported_placeholders("mission")
        dict_result = placeholders[0].to_dict()

        assert "placeholder" in dict_result
        assert "description" in dict_result
        assert "required" in dict_result
        assert "example" in dict_result


class TestHelperFunctions:
    """辅助函数测试"""

    def test_validate_prompt_function(self):
        """测试快捷验证函数"""
        result = validate_prompt("mission", "{date_str}")

        assert result.is_valid is True
        assert "{date_str}" in result.used_placeholders

    def test_get_placeholders_for_tool_function(self):
        """测试获取占位符函数"""
        placeholders = get_placeholders_for_tool("mission")

        assert len(placeholders) == 2
        assert isinstance(placeholders[0], dict)

    def test_get_placeholders_for_invalid_tool(self):
        """测试无效工具类型"""
        placeholders = get_placeholders_for_tool("invalid")
        assert len(placeholders) == 0


class TestValidationResultDataclass:
    """ValidationResult 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = ValidationResult(is_valid=True)

        assert result.errors == []
        assert result.warnings == []
        assert result.used_placeholders == []
        assert result.missing_placeholders == []
        assert result.unknown_placeholders == []

    def test_custom_values(self):
        """测试自定义值"""
        result = ValidationResult(
            is_valid=False,
            errors=["错误1"],
            warnings=["警告1"],
            used_placeholders=["{var}"],
        )

        assert result.is_valid is False
        assert result.errors == ["错误1"]
        assert result.warnings == ["警告1"]
        assert result.used_placeholders == ["{var}"]


class TestPlaceholderInfoDataclass:
    """PlaceholderInfo 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        info = PlaceholderInfo(placeholder="{test}", description="测试")

        assert info.required is False
        assert info.example == ""

    def test_custom_values(self):
        """测试自定义值"""
        info = PlaceholderInfo(
            placeholder="{query}",
            description="搜索词",
            required=True,
            example="test",
        )

        assert info.placeholder == "{query}"
        assert info.description == "搜索词"
        assert info.required is True
        assert info.example == "test"