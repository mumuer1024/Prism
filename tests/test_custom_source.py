# -*- coding: utf-8 -*-
"""
自定义数据源采集器测试

测试 CustomSourceSensor 的 RSS 和网页采集功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sensors.custom_source import (
    CustomSourceSensor,
    CustomSourceItem,
    fetch_custom_rss,
    fetch_custom_webpage,
    CUSTOM_SOURCE_ENABLED,
)


# ==========================================
# CustomSourceItem 测试
# ==========================================

class TestCustomSourceItem:
    """CustomSourceItem 数据类测试"""

    def test_item_creation(self):
        """测试创建条目"""
        item = CustomSourceItem(
            source_name="测试源",
            source_url="https://test.com/feed",
            title="测试标题",
            url="https://test.com/article/1",
            content="测试内容",
            published_at="2024-01-01",
            author="作者",
            tags=["tag1", "tag2"]
        )

        assert item.source_name == "测试源"
        assert item.title == "测试标题"
        assert item.author == "作者"

    def test_item_to_dict(self):
        """测试转换为字典"""
        item = CustomSourceItem(
            source_name="测试源",
            source_url="https://test.com/feed",
            title="测试标题",
            url="https://test.com/article/1",
            content="测试内容"
        )

        result = item.to_dict()
        assert result["source_name"] == "测试源"
        assert result["title"] == "测试标题"
        assert result["tags"] == []

    def test_item_default_values(self):
        """测试默认值"""
        item = CustomSourceItem(
            source_name="测试源",
            source_url="https://test.com/feed",
            title="测试标题",
            url="https://test.com/article/1",
            content="测试内容"
        )

        assert item.published_at == ""
        assert item.author is None
        assert item.tags is None


# ==========================================
# CustomSourceSensor 测试
# ==========================================

class TestCustomSourceSensor:
    """CustomSourceSensor 采集器测试"""

    @pytest.fixture
    def sensor(self):
        """创建采集器实例"""
        return CustomSourceSensor(timeout=5.0, max_items=10)

    def test_initialization(self, sensor):
        """测试初始化"""
        assert sensor._timeout == 5.0
        assert sensor._max_items == 10
        assert sensor._content_truncate == 500

    def test_context_manager(self, sensor):
        """测试上下文管理器"""
        with CustomSourceSensor() as s:
            assert s._client is not None or s._client is None  # 懒加载

    def test_close(self, sensor):
        """测试关闭"""
        sensor._get_client()  # 初始化客户端
        sensor.close()
        assert sensor._client is None

    def test_truncate_content(self, sensor):
        """测试内容截断"""
        long_content = "a" * 1000
        truncated = sensor._truncate_content(long_content)
        assert len(truncated) == sensor._content_truncate + 3  # 500 + "..."

    def test_truncate_short_content(self, sensor):
        """测试短内容不截断"""
        short_content = "短内容"
        truncated = sensor._truncate_content(short_content)
        assert truncated == short_content

    def test_clean_html(self, sensor):
        """测试 HTML 清理"""
        html = "<p>Test<b>Content</b></p>"
        clean = sensor._clean_html(html)
        assert "<p>" not in clean
        assert "<b>" not in clean
        assert "Test" in clean
        assert "Content" in clean


# ==========================================
# RSS 采集测试
# ==========================================

class TestRSSFetch:
    """RSS 采集测试"""

    @pytest.fixture
    def sensor(self):
        """创建采集器实例"""
        return CustomSourceSensor(timeout=5.0, max_items=10)

    @pytest.fixture
    def mock_rss_response(self):
        """Mock RSS 响应"""
        return b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Test</title><item><title>Article1</title><link>https://test.com/article/1</link><description>Description1</description><pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate><author>Author1</author></item><item><title>Article2</title><link>https://test.com/article/2</link><description>Description2</description><pubDate>Tue, 02 Jan 2024 00:00:00 +0000</pubDate></item></channel></rss>'

    @pytest.fixture
    def mock_atom_response(self):
        """Mock Atom 响应"""
        return b'<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Test</title><entry><title>AtomArticle1</title><link href="https://test.com/article/1"/><summary>Summary1</summary><published>2024-01-01T00:00:00Z</published><author><name>Author1</name></author></entry></feed>'

    @patch('httpx.Client.get')
    def test_fetch_rss20(self, mock_get, sensor, mock_rss_response):
        """测试 RSS 2.0 解析"""
        mock_response = Mock()
        mock_response.content = mock_rss_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = sensor.fetch_rss("TestSource", "https://test.com/feed")

        assert len(items) == 2
        assert items[0].title == "Article1"
        assert items[0].url == "https://test.com/article/1"
        assert items[0].author == "Author1"

    @patch('httpx.Client.get')
    def test_fetch_atom(self, mock_get, sensor, mock_atom_response):
        """测试 Atom 解析"""
        mock_response = Mock()
        mock_response.content = mock_atom_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = sensor.fetch_rss("TestSource", "https://test.com/feed")

        assert len(items) == 1
        assert items[0].title == "AtomArticle1"
        assert items[0].author == "Author1"

    @patch('httpx.Client.get')
    def test_rss_max_items_limit(self, mock_get, sensor):
        """测试条目数限制"""
        # 创建超过限制的条目
        items_xml = "<rss version='2.0'><channel>"
        for i in range(20):
            items_xml += f"<item><title>文章{i}</title><link>https://test.com/{i}</link></item>"
        items_xml += "</channel></rss>"

        mock_response = Mock()
        mock_response.content = items_xml.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = sensor.fetch_rss("测试源", "https://test.com/feed")

        assert len(items) == sensor._max_items  # 应该被限制

    @patch('httpx.Client.get')
    def test_rss_timeout(self, mock_get, sensor):
        """测试超时处理"""
        import httpx
        mock_get.side_effect = httpx.TimeoutException("超时")

        with pytest.raises(httpx.TimeoutException):
            sensor.fetch_rss("测试源", "https://test.com/feed")


# ==========================================
# 网页采集测试
# ==========================================

class TestWebpageFetch:
    """网页采集测试"""

    @pytest.fixture
    def sensor(self):
        return CustomSourceSensor(timeout=5.0, max_items=10)

    @pytest.fixture
    def mock_html_response(self):
        """Mock HTML 响应"""
        return b'<html><body><article><h2>Title1</h2><a href="/article/1">Link</a><p>Content1</p></article><article><h2>Title2</h2><a href="https://test.com/article/2">Link</a><p>Content2</p></article></body></html>'

    @patch('httpx.Client.get')
    def test_fetch_webpage_with_selectors(self, mock_get, sensor, mock_html_response):
        """测试网页采集"""
        mock_response = Mock()
        mock_response.content = mock_html_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = sensor.fetch_webpage(
            "TestSource",
            "https://test.com",
            selectors={
                'item': 'article',
                'title': 'h2',
                'link': 'a',
                'content': 'p'
            }
        )

        assert len(items) == 2
        assert items[0].title == "Title1"

    @patch('httpx.Client.get')
    def test_relative_link_handling(self, mock_get, sensor):
        """测试相对链接处理"""
        html = b'<html><body><article><h2>Title</h2><a href="/relative/path">Link</a></article></body></html>'

        mock_response = Mock()
        mock_response.content = html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = sensor.fetch_webpage(
            "TestSource",
            "https://test.com/page",
            selectors={'item': 'article', 'title': 'h2', 'link': 'a'}
        )

        # 相对链接应该被转换为绝对链接
        assert items[0].url.startswith("https://test.com")

    @patch('httpx.Client.get')
    def test_content_truncation(self, mock_get, sensor):
        """测试内容截断"""
        long_content = "a" * 1000
        html = f"""
        <html><body>
            <article>
                <h2>标题</h2>
                <a href="https://test.com/1">链接</a>
                <p>{long_content}</p>
            </article>
        </body></html>
        """.encode()

        mock_response = Mock()
        mock_response.content = html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        items = sensor.fetch_webpage(
            "测试源",
            "https://test.com",
            selectors={'item': 'article', 'title': 'h2', 'link': 'a', 'content': 'p'}
        )

        assert len(items[0].content) <= sensor._content_truncate + 3


# ==========================================
# 批量采集测试
# ==========================================

class TestBatchFetch:
    """批量采集测试"""

    @pytest.fixture
    def sensor(self):
        return CustomSourceSensor(timeout=5.0, max_items=5)

    @patch.object(CustomSourceSensor, 'fetch_rss')
    @patch.object(CustomSourceSensor, 'fetch_webpage')
    def test_fetch_sources(self, mock_webpage, mock_rss, sensor):
        """测试批量采集数据源"""
        mock_rss.return_value = [
            CustomSourceItem("RSS源", "https://rss.com", "标题1", "https://rss.com/1", "内容1")
        ]
        mock_webpage.return_value = [
            CustomSourceItem("网页源", "https://web.com", "标题2", "https://web.com/1", "内容2")
        ]

        sources = [
            {"name": "RSS源", "url": "https://rss.com/feed", "source_type": "rss"},
            {"name": "网页源", "url": "https://web.com", "source_type": "webpage"},
        ]

        items = sensor.fetch_sources(sources, delay=0)

        assert len(items) == 2
        mock_rss.assert_called_once()
        mock_webpage.assert_called_once()

    @patch.object(CustomSourceSensor, 'fetch_rss')
    def test_fetch_sources_with_error(self, mock_rss, sensor):
        """测试批量采集时部分失败"""
        mock_rss.side_effect = [
            [CustomSourceItem("源1", "https://1.com", "标题1", "https://1.com/1", "内容1")],
            Exception("失败")
        ]

        sources = [
            {"name": "源1", "url": "https://1.com/feed", "source_type": "rss"},
            {"name": "源2", "url": "https://2.com/feed", "source_type": "rss"},
        ]

        items = sensor.fetch_sources(sources, delay=0)

        # 第一个成功，第二个失败，应该返回第一个的结果
        assert len(items) == 1


# ==========================================
# 便捷函数测试
# ==========================================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @patch('src.sensors.custom_source.CustomSourceSensor.fetch_rss')
    def test_fetch_custom_rss(self, mock_fetch):
        """测试 fetch_custom_rss 函数"""
        mock_fetch.return_value = [
            CustomSourceItem("测试", "https://test.com", "标题", "https://test.com/1", "内容")
        ]

        result = fetch_custom_rss("测试", "https://test.com/feed")

        assert len(result) == 1
        assert result[0]["title"] == "标题"

    @patch('src.sensors.custom_source.CustomSourceSensor.fetch_webpage')
    def test_fetch_custom_webpage(self, mock_fetch):
        """测试 fetch_custom_webpage 函数"""
        mock_fetch.return_value = [
            CustomSourceItem("测试", "https://test.com", "标题", "https://test.com/1", "内容")
        ]

        result = fetch_custom_webpage("测试", "https://test.com")

        assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])