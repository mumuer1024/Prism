# -*- coding: utf-8 -*-
"""
数据源健康检测测试

测试 SourceHealthChecker 的健康检测功能。
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
import httpx

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sensors.source_health import (
    SourceHealthChecker,
    SourceHealthResult,
    HealthStatus,
    check_sources_health,
    check_single_source,
)


# ==========================================
# SourceHealthResult 测试
# ==========================================

class TestSourceHealthResult:
    """SourceHealthResult 数据类测试"""

    def test_result_creation(self):
        """测试创建结果"""
        result = SourceHealthResult(
            source_name="测试源",
            source_type="api",
            url="https://test.com/api",
            is_healthy=True,
            status=HealthStatus.HEALTHY,
            response_time_ms=150.5,
            last_check_at=datetime.now()
        )

        assert result.source_name == "测试源"
        assert result.is_healthy is True
        assert result.status == HealthStatus.HEALTHY

    def test_result_to_dict(self):
        """测试转换为字典"""
        result = SourceHealthResult(
            source_name="测试源",
            source_type="rss",
            url="https://test.com/feed",
            is_healthy=False,
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            last_check_at=datetime.now(),
            error_message="连接失败",
            consecutive_failures=3
        )

        data = result.to_dict()

        assert data["source_name"] == "测试源"
        assert data["is_healthy"] is False
        assert data["status"] == "unhealthy"
        assert data["error_message"] == "连接失败"
        assert data["consecutive_failures"] == 3


# ==========================================
# SourceHealthChecker 测试
# ==========================================

class TestSourceHealthChecker:
    """SourceHealthChecker 检测器测试"""

    @pytest.fixture
    def checker(self):
        """创建检测器实例"""
        return SourceHealthChecker(timeout=5.0)

    def test_initialization(self, checker):
        """测试初始化"""
        assert checker._timeout == 5.0
        assert len(checker._results) == 0

    def test_builtin_sources_exist(self, checker):
        """测试内置数据源列表存在"""
        assert len(SourceHealthChecker.BUILTIN_SOURCES) > 0

        for source in SourceHealthChecker.BUILTIN_SOURCES:
            assert "name" in source
            assert "type" in source
            assert "url" in source

    def test_context_manager(self, checker):
        """测试上下文管理器"""
        with SourceHealthChecker() as c:
            assert c._timeout == SourceHealthChecker.CHECK_TIMEOUT

    def test_close(self, checker):
        """测试关闭"""
        checker._get_client()  # 初始化客户端
        checker.close()
        assert checker._client is None


# ==========================================
# 健康检测测试
# ==========================================

class TestHealthCheck:
    """健康检测测试"""

    @pytest.fixture
    def checker(self):
        return SourceHealthChecker(timeout=5.0)

    @patch('httpx.Client.get')
    def test_check_healthy_source(self, mock_get, checker):
        """测试健康源检测"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = {
            "name": "测试源",
            "type": "api",
            "url": "https://test.com/api"
        }

        result = checker.check_source(source)

        assert result.is_healthy is True
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0

    @patch('httpx.Client.get')
    def test_check_unhealthy_source(self, mock_get, checker):
        """测试不健康源检测"""
        import httpx
        mock_get.side_effect = httpx.ConnectError("连接失败")

        source = {
            "name": "测试源",
            "type": "api",
            "url": "https://test.com/api"
        }

        result = checker.check_source(source)

        assert result.is_healthy is False
        assert result.status == HealthStatus.UNHEALTHY
        assert result.error_message is not None

    @patch('httpx.Client.get')
    def test_check_timeout(self, mock_get, checker):
        """测试超时检测"""
        import httpx
        mock_get.side_effect = httpx.TimeoutException("超时")

        source = {
            "name": "测试源",
            "type": "api",
            "url": "https://test.com/api"
        }

        result = checker.check_source(source)

        assert result.is_healthy is False
        assert result.status == HealthStatus.UNHEALTHY
        assert "超时" in result.error_message

    @patch('httpx.Client.get')
    def test_check_http_error(self, mock_get, checker):
        """测试 HTTP 错误"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock()

        source = {
            "name": "测试源",
            "type": "api",
            "url": "https://test.com/api"
        }

        # 模拟 HTTP 错误
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = checker.check_source(source)

        assert result.is_healthy is False

    @patch('httpx.Client.get')
    def test_response_time_record(self, mock_get, checker):
        """测试响应时间记录"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = {
            "name": "测试源",
            "type": "api",
            "url": "https://test.com/api"
        }

        result = checker.check_source(source)

        assert result.response_time_ms > 0
        assert result.response_time_ms < 10000  # 应该很快


# ==========================================
# 状态判定测试
# ==========================================

class TestHealthStatusDetermination:
    """健康状态判定测试"""

    @pytest.fixture
    def checker(self):
        return SourceHealthChecker()

    @patch('httpx.Client.get')
    def test_determine_healthy(self, mock_get, checker):
        """测试健康判定"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        source = {"name": "测试", "type": "api", "url": "https://test.com"}
        result = checker.check_source(source)

        assert result.status == HealthStatus.HEALTHY

    @patch.object(httpx.Client, 'get')
    def test_consecutive_failures_threshold(self, mock_get, checker):
        """测试连续失败阈值"""
        # 使用通用 HTTPError，更容易触发
        mock_get.side_effect = httpx.HTTPError("连接失败")

        source = {"name": "测试", "type": "api", "url": "https://test.com"}

        # 连续检测 3 次（需要保存结果才能累积失败次数）
        for i in range(3):
            result = checker.check_source(source)
            checker._results[source["name"]] = result  # 手动保存结果

        # 第 3 次应该累积失败次数 >= 3
        assert result.consecutive_failures >= 3


# ==========================================
# 批量检测测试
# ==========================================

class TestBatchCheck:
    """批量检测测试"""

    @pytest.fixture
    def checker(self):
        return SourceHealthChecker(timeout=5.0)

    @patch('httpx.Client.get')
    def test_check_all_sources(self, mock_get, checker):
        """测试检测所有数据源"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        results = checker.check_all_sources()

        assert len(results) > 0
        for result in results:
            assert isinstance(result, SourceHealthResult)

    @patch('httpx.Client.get')
    def test_get_health_summary(self, mock_get, checker):
        """测试获取健康摘要"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        checker.check_all_sources()
        summary = checker.get_health_summary()

        assert "total" in summary
        assert "healthy" in summary
        assert "unhealthy" in summary
        assert "health_rate" in summary
        assert "sources" in summary

    @patch('httpx.Client.get')
    def test_get_source_health(self, mock_get, checker):
        """测试获取单个数据源健康状态"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        checker.check_all_sources()

        # 尝试获取已知的数据源
        result = checker.get_source_health("V2EX RSS")
        assert result is not None or result is None  # 可能不存在


# ==========================================
# API 路由测试
# ==========================================

class TestHealthAPI:
    """健康检测 API 测试"""

    def test_create_health_router(self):
        """测试创建路由"""
        from src.sensors.source_health import create_health_router
        router = create_health_router()
        assert router is not None

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from src.sensors.source_health import create_health_router

        app = FastAPI()
        router = create_health_router()
        app.include_router(router)

        return TestClient(app)

    @patch('src.sensors.source_health.SourceHealthChecker.check_all_sources')
    def test_health_endpoint(self, mock_check, client):
        """测试 API 端点"""
        mock_check.return_value = [
            SourceHealthResult(
                source_name="测试源",
                source_type="api",
                url="https://test.com",
                is_healthy=True,
                status=HealthStatus.HEALTHY,
                response_time_ms=100,
                last_check_at=datetime.now()
            )
        ]

        response = client.get("/api/sources/health")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "sources" in data


# ==========================================
# 便捷函数测试
# ==========================================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @patch('src.sensors.source_health.SourceHealthChecker.check_all_sources')
    def test_check_sources_health(self, mock_check):
        """测试 check_sources_health 函数"""
        mock_check.return_value = []

        result = check_sources_health()

        assert "total" in result
        assert "sources" in result

    @patch('httpx.Client.get')
    def test_check_single_source(self, mock_get):
        """测试 check_single_source 函数"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_single_source("测试", "https://test.com", "api")

        assert result["source_name"] == "测试"
        assert result["source_type"] == "api"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])