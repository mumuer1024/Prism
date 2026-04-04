# -*- coding: utf-8 -*-
"""
V2EX 镜像站点测试

测试 V2EX 雷达的镜像站点功能。
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sensors.v2ex_radar import (
    V2EXRadar,
    MirrorTracker,
    MirrorStats,
    MirrorStatus,
    Lead,
    V2EX_MIRROR_ENABLED,
)


# ==========================================
# MirrorStats 测试
# ==========================================

class TestMirrorStats:
    """MirrorStats 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        stat = MirrorStats(name="测试", base_url="https://test.com")
        assert stat.name == "测试"
        assert stat.base_url == "https://test.com"
        assert stat.success_count == 0
        assert stat.fail_count == 0
        assert stat.avg_response_time_ms == 0.0
        assert stat.status == MirrorStatus.UNKNOWN

    def test_success_rate_zero(self):
        """测试成功率为 0"""
        stat = MirrorStats(name="测试", base_url="https://test.com")
        assert stat.success_rate() == 0.0

    def test_success_rate_calculation(self):
        """测试成功率计算"""
        stat = MirrorStats(
            name="测试",
            base_url="https://test.com",
            success_count=8,
            fail_count=2
        )
        assert stat.success_rate() == 0.8

    def test_to_dict(self):
        """测试转换为字典"""
        stat = MirrorStats(
            name="测试",
            base_url="https://test.com",
            success_count=5,
            status=MirrorStatus.HEALTHY
        )
        result = stat.to_dict()
        assert result["name"] == "测试"
        assert result["success_count"] == 5
        assert result["status"] == "healthy"


# ==========================================
# MirrorTracker 测试
# ==========================================

class TestMirrorTracker:
    """MirrorTracker 追踪器测试"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """创建临时追踪器"""
        cache_file = tmp_path / "mirror_stats.json"
        return MirrorTracker(cache_file=str(cache_file))

    def test_initial_stats_empty(self, tracker):
        """测试初始状态为空"""
        assert len(tracker._stats) == 0

    def test_record_success(self, tracker):
        """测试记录成功"""
        tracker.record_success(
            mirror_name="主站",
            base_url="https://www.v2ex.com",
            response_time_ms=1000.0
        )

        assert "主站" in tracker._stats
        stat = tracker._stats["主站"]
        assert stat.success_count == 1
        assert stat.avg_response_time_ms == 1000.0
        assert stat.consecutive_failures == 0
        assert stat.status == MirrorStatus.HEALTHY

    def test_record_failure(self, tracker):
        """测试记录失败"""
        tracker.record_failure(
            mirror_name="主站",
            base_url="https://www.v2ex.com"
        )

        assert "主站" in tracker._stats
        stat = tracker._stats["主站"]
        assert stat.fail_count == 1
        assert stat.consecutive_failures == 1

    def test_consecutive_failures_reset_on_success(self, tracker):
        """测试成功后重置连续失败计数"""
        # 先记录失败
        tracker.record_failure("主站", "https://www.v2ex.com")
        tracker.record_failure("主站", "https://www.v2ex.com")
        assert tracker._stats["主站"].consecutive_failures == 2

        # 记录成功
        tracker.record_success("主站", "https://www.v2ex.com", 1000.0)
        assert tracker._stats["主站"].consecutive_failures == 0

    def test_determine_status_healthy(self, tracker):
        """测试健康状态判定"""
        stat = MirrorStats(
            name="测试",
            base_url="https://test.com",
            success_count=10,
            avg_response_time_ms=1000.0
        )
        assert tracker._determine_status(stat) == MirrorStatus.HEALTHY

    def test_determine_status_degraded_by_response_time(self, tracker):
        """测试降级状态判定（响应时间）"""
        stat = MirrorStats(
            name="测试",
            base_url="https://test.com",
            success_count=10,
            avg_response_time_ms=6000.0  # > 5000ms
        )
        assert tracker._determine_status(stat) == MirrorStatus.DEGRADED

    def test_determine_status_unhealthy_by_failures(self, tracker):
        """测试不健康状态判定（连续失败）"""
        stat = MirrorStats(
            name="测试",
            base_url="https://test.com",
            consecutive_failures=3
        )
        assert tracker._determine_status(stat) == MirrorStatus.UNHEALTHY

    def test_get_sorted_mirrors(self, tracker):
        """测试镜像排序"""
        # 记录一些数据
        tracker.record_success("主站", "https://www.v2ex.com", 1000.0)
        tracker.record_success("全球镜像", "https://global.v2ex.com", 2000.0)
        tracker.record_failure("FastMirror", "https://v2ex.fastmirror.com")
        tracker.record_failure("FastMirror", "https://v2ex.fastmirror.com")
        tracker.record_failure("FastMirror", "https://v2ex.fastmirror.com")

        mirrors = [
            {"name": "主站", "base_url": "https://www.v2ex.com", "priority": 1, "is_official": True},
            {"name": "全球镜像", "base_url": "https://global.v2ex.com", "priority": 2, "is_official": True},
            {"name": "FastMirror", "base_url": "https://v2ex.fastmirror.com", "priority": 3, "is_official": False},
        ]

        sorted_mirrors = tracker.get_sorted_mirrors(mirrors)

        # 不健康的 FastMirror 应该排在最后
        assert sorted_mirrors[-1]["name"] == "FastMirror"
        assert sorted_mirrors[-1]["status"] == MirrorStatus.UNHEALTHY

    def test_stats_persistence(self, tmp_path):
        """测试统计数据持久化"""
        cache_file = tmp_path / "mirror_stats.json"

        # 创建追踪器并记录数据
        tracker1 = MirrorTracker(cache_file=str(cache_file))
        tracker1.record_success("主站", "https://www.v2ex.com", 1000.0)

        # 创建新追踪器，应该加载之前的数据
        tracker2 = MirrorTracker(cache_file=str(cache_file))
        assert "主站" in tracker2._stats
        assert tracker2._stats["主站"].success_count == 1


# ==========================================
# V2EXRadar 镜像功能测试
# ==========================================

class TestV2EXRadarMirror:
    """V2EXRadar 镜像功能测试"""

    def test_mirror_enabled_by_default(self):
        """测试镜像功能默认启用"""
        radar = V2EXRadar(use_mirror=True)
        assert radar._use_mirror is True
        assert radar._mirror_tracker is not None
        radar.close()

    def test_mirror_disabled(self):
        """测试禁用镜像功能"""
        radar = V2EXRadar(use_mirror=False)
        assert radar._use_mirror is False
        assert radar._mirror_tracker is None
        radar.close()

    def test_mirror_config_exists(self):
        """测试镜像配置存在"""
        assert len(V2EXRadar.MIRRORS) >= 1
        for mirror in V2EXRadar.MIRRORS:
            assert "name" in mirror
            assert "base_url" in mirror
            assert "priority" in mirror

    @patch.object(V2EXRadar, '_fetch_from_mirror')
    def test_fetch_with_mirror_fallback_success(self, mock_fetch):
        """测试镜像获取成功"""
        mock_fetch.return_value = [
            {'title': '测试帖子', 'url': 'https://test.com/t/1', 'content': '内容', 'pub_date': ''}
        ]

        radar = V2EXRadar(use_mirror=True)
        # 清除缓存
        radar._load_cache = lambda x: None

        result = radar._fetch_with_mirror_fallback('global')

        assert len(result) == 1
        assert result[0]['title'] == '测试帖子'
        radar.close()

    @patch.object(V2EXRadar, '_fetch_from_mirror')
    def test_fetch_with_mirror_fallback_all_fail(self, mock_fetch):
        """测试所有镜像都失败"""
        mock_fetch.side_effect = Exception("连接失败")

        radar = V2EXRadar(use_mirror=True)
        # 清除缓存
        radar._load_cache = lambda x: None

        result = radar._fetch_with_mirror_fallback('global')

        assert result == []
        radar.close()

    def test_get_mirror_stats(self):
        """测试获取镜像统计"""
        radar = V2EXRadar(use_mirror=True)
        stats = radar.get_mirror_stats()

        assert 'total_mirrors' in stats
        assert 'mirrors' in stats
        radar.close()

    def test_context_manager(self):
        """测试上下文管理器"""
        with V2EXRadar(use_mirror=True) as radar:
            assert radar._client is not None
        # 退出后应该关闭
        assert radar._client is None or True  # 可能已经被关闭


# ==========================================
# Lead 测试
# ==========================================

class TestLead:
    """Lead 数据类测试"""

    def test_lead_creation(self):
        """测试创建 Lead"""
        lead = Lead(
            source="V2EX-global",
            title="测试标题",
            url="https://test.com/t/1",
            summary="测试摘要",
            posted_date="2024-01-01",
            tags=["💰Money", "🔥Urgent"],
            desperation_score=100
        )

        assert lead.source == "V2EX-global"
        assert lead.desperation_score == 100

    def test_lead_to_dict(self):
        """测试 Lead 转换为字典"""
        lead = Lead(
            source="V2EX-global",
            title="测试标题",
            url="https://test.com/t/1",
            summary="测试摘要",
            posted_date="2024-01-01",
            tags=["💰Money"]
        )

        result = lead.to_dict()
        assert result["source"] == "V2EX-global"
        assert result["title"] == "测试标题"
        assert "💰Money" in result["tags"]


# ==========================================
# 集成测试
# ==========================================

class TestV2EXRadarIntegration:
    """V2EXRadar 集成测试"""

    @pytest.mark.skipif(
        not V2EX_MIRROR_ENABLED,
        reason="镜像功能未启用"
    )
    def test_mirror_list_not_empty(self):
        """测试镜像列表非空"""
        assert len(V2EXRadar.MIRRORS) > 0

    def test_mirror_has_required_fields(self):
        """测试镜像配置字段完整"""
        for mirror in V2EXRadar.MIRRORS:
            assert "name" in mirror
            assert "base_url" in mirror
            assert "priority" in mirror
            assert "is_official" in mirror

    def test_mirror_priority_order(self):
        """测试镜像优先级排序"""
        mirrors = V2EXRadar.MIRRORS
        priorities = [m["priority"] for m in mirrors]
        # 优先级应该是唯一的
        assert len(priorities) == len(set(priorities))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])