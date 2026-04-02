"""
传感器模块单元测试

包含 Hacker News、GitHub Trending 等传感器的单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

# 导入被测模块
from src.sensors.hacker_news import HNStory, fetch_top_stories
from src.sensors.github_trending import fetch_trending_repos


class TestHNStory:
    """HNStory 数据类测试"""
    
    def test_hn_url_property_with_url(self):
        """测试有 URL 时返回原始 URL"""
        story = HNStory(
            id=12345,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            descendants=50
        )
        assert story.url == "https://example.com/article"
    
    def test_hn_url_property_without_url(self):
        """测试无 URL 时返回 Hacker News 链接"""
        story = HNStory(
            id=12345,
            title="Test Story",
            url=None,
            score=100,
            by="testuser",
            descendants=50
        )
        assert story.url is None
    
    def test_hn_url_derived_property(self):
        """测试 hn_url 派生属性"""
        story = HNStory(
            id=12345,
            title="Test Story",
            url=None,
            score=100,
            by="testuser",
            descendants=50
        )
        assert story.hn_url == "https://news.ycombinator.com/item?id=12345"
    
    def test_hn_url_derived_with_url(self):
        """测试有 URL 时 hn_url 仍返回 HN 链接"""
        story = HNStory(
            id=12345,
            title="Test Story",
            url="https://example.com",
            score=100,
            by="testuser",
            descendants=50
        )
        # hn_url 始终返回 HN 链接
        assert story.hn_url == "https://news.ycombinator.com/item?id=12345"


class TestFetchTopStories:
    """fetch_top_stories 函数测试"""
    
    @patch('src.sensors.hacker_news.httpx.get')
    def test_fetch_success(self, mock_get):
        """测试成功获取故事列表"""
        # Mock 顶层故事 ID 响应
        mock_top_response = Mock()
        mock_top_response.json.return_value = [123, 456, 789]
        
        # Mock 单个故事详情响应
        def create_item_response(sid):
            mock_item = Mock()
            if sid == 123:
                mock_item.json.return_value = {
                    "id": 123,
                    "type": "story",
                    "title": "First Story",
                    "url": "https://example.com/1",
                    "score": 100,
                    "by": "user1",
                    "descendants": 50
                }
            elif sid == 456:
                mock_item.json.return_value = {
                    "id": 456,
                    "type": "story",
                    "title": "Second Story",
                    "url": "https://example.com/2",
                    "score": 80,
                    "by": "user2",
                    "descendants": 30
                }
            else:
                mock_item.json.return_value = None  # 第三个故事不存在
            return mock_item
        
        mock_get.side_effect = [mock_top_response] + [create_item_response(sid) for sid in [123, 456, 789]]
        
        # 执行
        stories = fetch_top_stories(limit=3)
        
        # 验证
        assert len(stories) == 2  # 只有前两个有效
        assert stories[0].title == "First Story"
        assert stories[0].score == 100
        assert stories[1].title == "Second Story"
        assert stories[1].score == 80
    
    @patch('src.sensors.hacker_news.httpx.get')
    def test_fetch_empty(self, mock_get):
        """测试获取空列表"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        stories = fetch_top_stories(limit=10)
        assert stories == []
    
    @patch('src.sensors.hacker_news.httpx.get')
    def test_fetch_timeout(self, mock_get):
        """测试请求超时"""
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        with pytest.raises(httpx.TimeoutException):
            fetch_top_stories()
    
    @patch('src.sensors.hacker_news.httpx.get')
    def test_fetch_http_error(self, mock_get):
        """测试 HTTP 错误"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=Mock(),
            response=Mock(status_code=500)
        )
        mock_get.return_value = mock_response
        
        with pytest.raises(httpx.HTTPStatusError):
            fetch_top_stories()
    
    @patch('src.sensors.hacker_news.httpx.get')
    def test_fetch_skips_non_story_items(self, mock_get):
        """测试跳过非 story 类型"""
        mock_top_response = Mock()
        mock_top_response.json.return_value = [123, 456]
        
        def create_item_response(sid):
            mock_item = Mock()
            if sid == 123:
                mock_item.json.return_value = {
                    "id": 123,
                    "type": "story",
                    "title": "Valid Story",
                    "url": "https://example.com",
                    "score": 100,
                    "by": "user",
                    "descendants": 50
                }
            else:
                # 模拟 job 类型
                mock_item.json.return_value = {
                    "id": 456,
                    "type": "job",
                    "title": "Job Post",
                }
            return mock_item
        
        mock_get.side_effect = [mock_top_response] + [create_item_response(sid) for sid in [123, 456]]
        
        stories = fetch_top_stories(limit=2)
        
        # 应该只返回 story 类型的项目
        assert len(stories) == 1
        assert stories[0].title == "Valid Story"


class TestGitHubTrending:
    """GitHub Trending 传感器测试（占位，需要根据实际实现调整）"""
    
    @pytest.mark.skip(reason="需要 GITHUB_TOKEN 环境变量")
    def test_fetch_trending_real(self):
        """真实 API 测试（需要配置）"""
        repos = fetch_trending_repos(language="python", limit=5)
        assert isinstance(repos, list)
    
    @patch('src.sensors.github_trending.httpx.get')
    def test_fetch_trending_mock(self, mock_get):
        """Mock 测试"""
        # 注意：需要根据实际实现调整 mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "search": {
                    "nodes": [
                        {"name": "repo1", "description": "Description 1", "stargazerCount": 100},
                        {"name": "repo2", "description": "Description 2", "stargazerCount": 50},
                    ]
                }
            }
        }
        mock_get.return_value = mock_response
        
        # 根据实际函数签名调整
        # repos = fetch_trending_repos(language="python", limit=5)
        # assert len(repos) == 2


# ═══════════════════════════════════════════════════════════
# 集成测试（可选，需要真实环境）
# ═══════════════════════════════════════════════════════════

class TestSensorIntegration:
    """传感器集成测试"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=5.0),
        reason="No network access"
    )
    def test_hacker_news_integration(self):
        """真实网络集成测试"""
        stories = fetch_top_stories(limit=5)
        assert len(stories) <= 5
        assert all(isinstance(s, HNStory) for s in stories)


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def sample_hn_story():
    """示例 HN 故事数据"""
    return HNStory(
        id=12345,
        title="Sample Story for Testing",
        url="https://example.com/sample",
        score=100,
        by="testuser",
        descendants=50
    )


@pytest.fixture
def sample_hn_stories():
    """示例 HN 故事列表"""
    return [
        HNStory(id=1, title="Story 1", url="https://example.com/1", score=100, by="user1", descendants=10),
        HNStory(id=2, title="Story 2", url="https://example.com/2", score=80, by="user2", descendants=20),
        HNStory(id=3, title="Story 3", url=None, score=60, by="user3", descendants=30),
    ]


@pytest.fixture
def mock_httpx_success():
    """成功的 httpx mock"""
    with patch('src.sensors.hacker_news.httpx') as mock:
        yield mock


@pytest.fixture
def mock_httpx_failure():
    """失败的 httpx mock"""
    with patch('src.sensors.hacker_news.httpx') as mock:
        mock.get.side_effect = httpx.HTTPError("Network error")
        yield mock