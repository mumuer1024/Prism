# -*- coding: utf-8 -*-
"""
DailyHotApi Sensor 单元测试

测试热榜数据传感器的核心功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from src.sensors.dailyhot_sensor import (
    DailyHotSensor,
    HotItem,
    CATEGORY_MAP,
    ALL_PLATFORMS,
    fetch_dailyhot,
    test_dailyhot_connection,
)
from src.config_loader import DEFAULT_DAILYHOT_CATEGORIES


class TestCategoryMap:
    """测试分类映射结构"""

    def test_category_map_has_four_categories(self):
        """验证 CATEGORY_MAP 包含 4 个分类"""
        assert len(CATEGORY_MAP) == 4
        assert "tech" in CATEGORY_MAP
        assert "dev" in CATEGORY_MAP
        assert "news" in CATEGORY_MAP
        assert "entertainment" in CATEGORY_MAP

    def test_category_map_structure(self):
        """验证每个分类有 label 和 platforms"""
        for key, data in CATEGORY_MAP.items():
            assert "label" in data, f"分类 {key} 缺少 label"
            assert "platforms" in data, f"分类 {key} 缺少 platforms"
            assert isinstance(data["label"], str)
            assert isinstance(data["platforms"], list)
            assert len(data["platforms"]) > 0, f"分类 {key} 的 platforms 为空"

    def test_platform_structure(self):
        """验证每个平台有 key 和 name"""
        for key, data in CATEGORY_MAP.items():
            for platform in data["platforms"]:
                assert "key" in platform, f"分类 {key} 的平台缺少 key"
                assert "name" in platform, f"分类 {key} 的平台缺少 name"

    def test_all_platforms_not_empty(self):
        """验证 ALL_PLATFORMS 不为空"""
        assert len(ALL_PLATFORMS) > 0


class TestHotItem:
    """测试 HotItem 数据结构"""

    def test_hot_item_creation(self):
        """测试 HotItem 创建"""
        item = HotItem(
            title="测试标题",
            url="https://example.com",
            hot=12345,
            timestamp=1700000000000,
            source="知乎",
            source_key="zhihu",
            category="news",
        )
        assert item.title == "测试标题"
        assert item.hot == 12345
        assert item.source == "知乎"

    def test_hot_item_to_dict(self):
        """测试 HotItem 转换为字典"""
        item = HotItem(
            title="测试标题",
            url="https://example.com",
            hot=12345,
            timestamp=1700000000000,
            source="知乎",
            source_key="zhihu",
            category="news",
        )
        data = item.to_dict()
        assert isinstance(data, dict)
        assert data["title"] == "测试标题"
        assert data["hot"] == 12345
        assert data["source"] == "知乎"


class TestDailyHotSensor:
    """测试 DailyHotSensor 类"""

    def test_base_url_from_settings(self):
        """验证 base_url 从 settings 读取"""
        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            assert sensor.base_url == "https://test.example.com"

    def test_get_category_map(self):
        """测试获取分类映射"""
        sensor = DailyHotSensor()
        category_map = sensor.get_category_map()
        assert category_map == CATEGORY_MAP
        assert "tech" in category_map

    def test_get_platform_name(self):
        """测试获取平台名称"""
        sensor = DailyHotSensor()
        assert sensor._get_platform_name("zhihu") == "知乎"
        assert sensor._get_platform_name("bilibili") == "哔哩哔哩"
        assert sensor._get_platform_name("unknown") == "unknown"

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_platform_success(self, mock_get):
        """测试成功获取单个平台数据"""
        # Mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": [
                {
                    "title": "测试新闻1",
                    "url": "https://example.com/1",
                    "hot": 10000,
                    "timestamp": 1700000000,
                },
                {
                    "title": "测试新闻2",
                    "url": "https://example.com/2",
                    "hot": "5万",
                },
            ]
        }
        mock_get.return_value = mock_response

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_platform("zhihu", limit=10, category="news")

        assert len(items) == 2
        assert items[0].title == "测试新闻1"
        assert items[0].source == "知乎"
        assert items[0].category == "news"

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_platform_error_status(self, mock_get):
        """测试 API 返回错误状态码"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_platform("zhihu")

        assert items == []

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_platform_timeout(self, mock_get):
        """测试请求超时"""
        mock_get.side_effect = httpx.TimeoutException("Timeout")

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_platform("zhihu")

        assert items == []

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_platform_request_error(self, mock_get):
        """测试请求错误"""
        mock_get.side_effect = httpx.RequestError("Connection error")

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_platform("zhihu")

        assert items == []

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_platform_invalid_response(self, mock_get):
        """测试无效响应格式"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 500, "message": "error"}
        mock_get.return_value = mock_response

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_platform("zhihu")

        assert items == []


class TestHotValueParsing:
    """测试热度值解析"""

    def test_parse_hot_integer(self):
        """测试整数热度解析"""
        sensor = DailyHotSensor()
        item = sensor._parse_item(
            {"title": "测试", "url": "https://example.com", "hot": 12345},
            "zhihu", "知乎", "news"
        )
        assert item.hot == 12345

    def test_parse_hot_wan(self):
        """测试"万"格式热度解析"""
        sensor = DailyHotSensor()
        item = sensor._parse_item(
            {"title": "测试", "url": "https://example.com", "hot": "5万"},
            "zhihu", "知乎", "news"
        )
        assert item.hot == 50000

    def test_parse_hot_yi(self):
        """测试"亿"格式热度解析"""
        sensor = DailyHotSensor()
        item = sensor._parse_item(
            {"title": "测试", "url": "https://example.com", "hot": "1.5亿"},
            "zhihu", "知乎", "news"
        )
        assert item.hot == 150000000

    def test_parse_hot_with_comma(self):
        """测试带逗号的热度解析"""
        sensor = DailyHotSensor()
        item = sensor._parse_item(
            {"title": "测试", "url": "https://example.com", "hot": "12,345"},
            "zhihu", "知乎", "news"
        )
        assert item.hot == 12345

    def test_parse_hot_none(self):
        """测试无热度值"""
        sensor = DailyHotSensor()
        item = sensor._parse_item(
            {"title": "测试", "url": "https://example.com"},
            "zhihu", "知乎", "news"
        )
        assert item.hot == 0


class TestFetchByCategories:
    """测试按分类获取数据"""

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_by_categories_default(self, mock_get):
        """测试默认分类获取"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "data": [
                {"title": "测试", "url": "https://example.com", "hot": 1000}
            ]
        }
        mock_get.return_value = mock_response

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_by_categories(["tech"], limit_per_platform=5)

        # tech 分类有 4 个平台
        assert mock_get.call_count == 4

    @patch('src.sensors.dailyhot_sensor.httpx.get')
    def test_fetch_by_categories_sorted_by_hot(self, mock_get):
        """测试结果按热度排序"""
        call_count = [0]

        def mock_response_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_resp = Mock()
            mock_resp.status_code = 200
            # 不同平台返回不同热度
            hot_values = [100, 500, 300, 200]
            idx = (call_count[0] - 1) % 4
            mock_resp.json.return_value = {
                "code": 200,
                "data": [
                    {"title": f"测试{idx}", "url": "https://example.com", "hot": hot_values[idx]}
                ]
            }
            return mock_resp

        mock_get.side_effect = mock_response_side_effect

        with patch('src.sensors.dailyhot_sensor.settings') as mock_settings:
            mock_settings.DAILYHOT_API_URL = "https://test.example.com"
            sensor = DailyHotSensor()
            items = sensor.fetch_by_categories(["tech"], limit_per_platform=5)

        # 验证按热度降序排列
        if len(items) > 1:
            for i in range(len(items) - 1):
                assert items[i].hot >= items[i + 1].hot


class TestConvenienceFunctions:
    """测试便捷函数"""

    @patch('src.sensors.dailyhot_sensor.DailyHotSensor.fetch_by_categories')
    def test_fetch_dailyhot_default(self, mock_fetch):
        """测试 fetch_dailyhot 默认参数"""
        mock_fetch.return_value = []
        result = fetch_dailyhot()
        mock_fetch.assert_called_once_with(["tech", "dev"], 10)

    @patch('src.sensors.dailyhot_sensor.DailyHotSensor.fetch_by_categories')
    def test_fetch_dailyhot_custom(self, mock_fetch):
        """测试 fetch_dailyhot 自定义参数"""
        mock_fetch.return_value = []
        result = fetch_dailyhot(categories=["news"], limit=20)
        mock_fetch.assert_called_once_with(["news"], 20)

    @patch('src.sensors.dailyhot_sensor.DailyHotSensor.test_connection')
    def test_test_dailyhot_connection(self, mock_test):
        """测试连接测试函数"""
        mock_test.return_value = {"zhihu": True, "bilibili": False}
        result = test_dailyhot_connection()
        assert result["zhihu"] is True
        assert result["bilibili"] is False


class TestDefaultCategories:
    """测试默认分类配置"""

    def test_default_categories_value(self):
        """验证默认分类值"""
        assert DEFAULT_DAILYHOT_CATEGORIES == ["tech", "dev"]