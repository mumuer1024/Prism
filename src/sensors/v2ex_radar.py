# -*- coding: utf-8 -*-
"""
V2EX 雷达传感器（优化版 V2）

功能：
- 多镜像站点支持（主站 → 全球镜像 → 第三方镜像）
- 多数据源 fallback（RSS → API）
- 站点性能追踪（响应时间、成功率）
- 请求重试机制
- 本地缓存（1小时）
- 正确关闭 HTTP 客户端
- 结构化日志
- 配置开关支持
"""

import httpx
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import datetime
import re
import sys
import json
import logging
import os
import time
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Ensure UTF-8 output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 配置日志
logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = Path(__file__).parent.parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


# ==========================================
# 配置开关
# ==========================================

def _parse_bool(val: str | None, default: bool = True) -> bool:
    """解析布尔值"""
    if val is None:
        return default
    return val.lower() in ('true', 'yes', '1', 'on', 'enabled')

# 镜像功能开关（可通过环境变量禁用）
V2EX_MIRROR_ENABLED = _parse_bool(os.getenv("V2EX_MIRROR_ENABLED"), True)


# ==========================================
# 镜像站点状态枚举
# ==========================================

class MirrorStatus(Enum):
    """镜像站点状态"""
    HEALTHY = "healthy"      # 健康，可正常使用
    DEGRADED = "degraded"    # 降级，响应慢但可用
    UNHEALTHY = "unhealthy"  # 不健康，暂停使用
    UNKNOWN = "unknown"      # 未检测


# ==========================================
# 镜像站点统计
# ==========================================

@dataclass
class MirrorStats:
    """镜像站点统计数据"""
    name: str
    base_url: str
    priority: int = 1
    is_official: bool = True
    success_count: int = 0
    fail_count: int = 0
    avg_response_time_ms: float = 0.0
    total_response_time_ms: float = 0.0
    last_success_at: Optional[str] = None
    last_fail_at: Optional[str] = None
    consecutive_failures: int = 0
    status: MirrorStatus = MirrorStatus.UNKNOWN

    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0.0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "priority": self.priority,
            "is_official": self.is_official,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "success_rate": self.success_rate(),
            "avg_response_time_ms": self.avg_response_time_ms,
            "last_success_at": self.last_success_at,
            "last_fail_at": self.last_fail_at,
            "consecutive_failures": self.consecutive_failures,
            "status": self.status.value,
        }


class MirrorTracker:
    """
    镜像站点追踪器

    记录各镜像站点的性能数据，支持：
    - 成功/失败记录
    - 响应时间统计
    - 状态判定
    - 数据持久化
    """

    # 状态判定阈值
    RESPONSE_TIME_DEGRADED_MS = 5000   # 降级阈值
    RESPONSE_TIME_UNHEALTHY_MS = 10000  # 不健康阈值
    CONSECUTIVE_FAILURES_THRESHOLD = 3  # 连续失败阈值

    def __init__(self, cache_file: str = "cache/v2ex_mirror_stats.json"):
        self._cache_file = CACHE_DIR / "v2ex_mirror_stats.json"
        self._stats: Dict[str, MirrorStats] = {}
        self._load_stats()

    def _load_stats(self):
        """从文件加载统计数据"""
        if not self._cache_file.exists():
            return

        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for name, stat_data in data.get('mirrors', {}).items():
                self._stats[name] = MirrorStats(
                    name=name,
                    base_url=stat_data.get('base_url', ''),
                    priority=stat_data.get('priority', 1),
                    is_official=stat_data.get('is_official', True),
                    success_count=stat_data.get('success_count', 0),
                    fail_count=stat_data.get('fail_count', 0),
                    avg_response_time_ms=stat_data.get('avg_response_time_ms', 0.0),
                    total_response_time_ms=stat_data.get('total_response_time_ms', 0.0),
                    last_success_at=stat_data.get('last_success_at'),
                    last_fail_at=stat_data.get('last_fail_at'),
                    consecutive_failures=stat_data.get('consecutive_failures', 0),
                    status=MirrorStatus(stat_data.get('status', 'unknown')),
                )

            logger.info(f"镜像统计数据加载完成: {len(self._stats)} 个站点")

        except Exception as e:
            logger.warning(f"镜像统计数据加载失败: {e}")

    def _save_stats(self):
        """保存统计数据到文件"""
        try:
            data = {
                'updated_at': datetime.datetime.now().isoformat(),
                'mirrors': {name: stat.to_dict() for name, stat in self._stats.items()}
            }

            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"镜像统计数据已保存")

        except Exception as e:
            logger.warning(f"镜像统计数据保存失败: {e}")

    def record_success(self, mirror_name: str, base_url: str, response_time_ms: float,
                       priority: int = 1, is_official: bool = True):
        """记录成功请求"""
        now = datetime.datetime.now().isoformat()

        if mirror_name not in self._stats:
            self._stats[mirror_name] = MirrorStats(
                name=mirror_name,
                base_url=base_url,
                priority=priority,
                is_official=is_official,
            )

        stat = self._stats[mirror_name]
        stat.success_count += 1
        stat.total_response_time_ms += response_time_ms
        stat.avg_response_time_ms = stat.total_response_time_ms / stat.success_count
        stat.last_success_at = now
        stat.consecutive_failures = 0  # 重置连续失败计数

        # 更新状态
        stat.status = self._determine_status(stat)

        self._save_stats()
        logger.debug(f"镜像成功: {mirror_name}, 响应时间: {response_time_ms:.0f}ms")

    def record_failure(self, mirror_name: str, base_url: str,
                       priority: int = 1, is_official: bool = True):
        """记录失败请求"""
        now = datetime.datetime.now().isoformat()

        if mirror_name not in self._stats:
            self._stats[mirror_name] = MirrorStats(
                name=mirror_name,
                base_url=base_url,
                priority=priority,
                is_official=is_official,
            )

        stat = self._stats[mirror_name]
        stat.fail_count += 1
        stat.last_fail_at = now
        stat.consecutive_failures += 1

        # 更新状态
        stat.status = self._determine_status(stat)

        self._save_stats()
        logger.debug(f"镜像失败: {mirror_name}, 连续失败: {stat.consecutive_failures}")

    def _determine_status(self, stat: MirrorStats) -> MirrorStatus:
        """判定站点状态"""
        # 连续失败 >= 3：不健康
        if stat.consecutive_failures >= self.CONSECUTIVE_FAILURES_THRESHOLD:
            return MirrorStatus.UNHEALTHY

        # 响应时间 > 10s：不健康
        if stat.avg_response_time_ms > self.RESPONSE_TIME_UNHEALTHY_MS:
            return MirrorStatus.UNHEALTHY

        # 响应时间 > 5s：降级
        if stat.avg_response_time_ms > self.RESPONSE_TIME_DEGRADED_MS:
            return MirrorStatus.DEGRADED

        # 有失败记录但未达阈值：降级
        if stat.fail_count > 0 and stat.success_count > 0:
            if stat.success_rate() < 0.8:
                return MirrorStatus.DEGRADED

        # 正常
        if stat.success_count > 0:
            return MirrorStatus.HEALTHY

        return MirrorStatus.UNKNOWN

    def get_sorted_mirrors(self, mirror_configs: List[Dict]) -> List[Dict]:
        """
        获取排序后的镜像列表

        排序规则：
        1. 不健康站点排到最后
        2. 按优先级排序
        3. 同优先级按响应时间排序

        Args:
            mirror_configs: 镜像配置列表

        Returns:
            排序后的镜像配置列表（包含状态信息）
        """
        sorted_mirrors = []

        for config in mirror_configs:
            name = config['name']
            stat = self._stats.get(name)

            mirror_with_status = {
                **config,
                'status': stat.status if stat else MirrorStatus.UNKNOWN,
                'avg_response_time_ms': stat.avg_response_time_ms if stat else 0,
                'consecutive_failures': stat.consecutive_failures if stat else 0,
            }
            sorted_mirrors.append(mirror_with_status)

        # 排序：不健康排最后，然后按优先级+响应时间
        def sort_key(m):
            # 不健康站点权重最低
            status_weight = 0 if m['status'] == MirrorStatus.HEALTHY else \
                           1 if m['status'] == MirrorStatus.DEGRADED else 2
            # 优先级（数字越小优先级越高）
            priority = m['priority']
            # 响应时间（越小越好）
            response_time = m['avg_response_time_ms']
            return (status_weight, priority, response_time)

        sorted_mirrors.sort(key=sort_key)
        return sorted_mirrors

    def get_stats_summary(self) -> Dict:
        """获取统计摘要"""
        return {
            'total_mirrors': len(self._stats),
            'mirrors': [stat.to_dict() for stat in self._stats.values()],
        }


@dataclass
class Lead:
    """V2EX 商机线索"""
    source: str
    title: str
    url: str
    summary: str
    posted_date: str
    tags: List[str]
    desperation_score: int = 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "posted_date": self.posted_date,
            "tags": self.tags,
            "desperation_score": self.desperation_score,
        }


class V2EXRadar:
    """
    V2EX 商机雷达（优化版 V2）

    扫描 V2EX 寻找外包、兼职、求助等商机线索。

    优化特性：
    - 多镜像站点：主站 → 全球镜像 → 第三方镜像
    - 多数据源：RSS Feed → 官方 API fallback
    - 站点性能追踪：响应时间、成功率
    - 请求重试：网络错误自动重试 2 次
    - 本地缓存：缓存 1 小时，减少请求
    - 连接管理：正确关闭 HTTP 客户端
    """

    # ==========================================
    # 镜像站点配置
    # ==========================================

    MIRRORS = [
        {
            "name": "主站",
            "base_url": "https://www.v2ex.com",
            "priority": 1,
            "region": "cn",
            "is_official": True,
        },
        {
            "name": "全球镜像",
            "base_url": "https://global.v2ex.com",
            "priority": 2,
            "region": "global",
            "is_official": True,
        },
        {
            "name": "FastMirror",
            "base_url": "https://v2ex.fastmirror.com",
            "priority": 3,
            "region": "global",
            "is_official": False,  # 第三方镜像
        },
    ]

    # RSS 数据源（相对路径）
    RSS_PATHS = {
        "global": "/index.xml",
        "jobs": "/feed/tab/jobs.xml"
    }

    # 官方 API 数据源（相对路径）
    API_PATHS = {
        "hot": "/api/topics/hot.json",
        "latest": "/api/topics/latest.json",
    }

    # 兼容旧版配置
    RSS_FEEDS = {
        "global": "https://www.v2ex.com/index.xml",
        "jobs": "https://www.v2ex.com/feed/tab/jobs.xml"
    }

    API_ENDPOINTS = {
        "hot": "https://www.v2ex.com/api/topics/hot.json",
        "latest": "https://www.v2ex.com/api/topics/latest.json",
    }

    # 关键词配置
    DEFAULT_MONEY_KEYWORDS = [
        "外包", "兼职", "有偿", "预算", "报价", "招", "急", "付费",
        "代写", "私活", "合作", "开发", "求购", "悬赏", "报酬",
        "价格", "费用", "多少钱", "收费", "接单", "项目", "甲方"
    ]

    DEFAULT_PAIN_KEYWORDS = [
        "求助", "帮忙", "不懂", "救命", "怎么做", "太难", "崩溃", "无法", "报错",
        "不会", "求教", "求大佬", "有没有人", "小白", "新手", "搞不定",
        "折腾", "卡住", "解决不了", "求指导", "求解答", "头疼"
    ]

    DEFAULT_DESPERATION_KEYWORDS = [
        "在线等", "有偿", "急", "救命", "红包", "崩溃", "求大佬", "付费解决",
        "今晚", "明天", "截止", "最后", "加急", "马上", "立刻", "紧急",
        "求求", "跪求", "在线等", "速回"
    ]

    DEFAULT_TECH_KEYWORDS = [
        "FPGA", "Verilog", "Python", "爬虫", "脚本", "Web3", "Solana",
        "Rust", "图像", "视觉", "识别", "抠图", "Automation", "Bot",
        "Vue", "React", "Node", "Java", "Go", "TypeScript", "小程序",
        "App", "网站", "后端", "前端", "数据库", "API", "自动化",
        "Chrome", "插件", "扩展", "爬虫", "数据采集", "机器学习", "AI"
    ]

    def __init__(
        self,
        custom_keywords: dict = None,
        cache_hours: int = 1,
        timeout: float = 15.0,
        use_mirror: bool = None,
    ):
        """
        初始化 V2EX 雷达

        Args:
            custom_keywords: 自定义关键词配置
            cache_hours: 缓存有效期（小时）
            timeout: HTTP 请求超时时间
            use_mirror: 是否使用镜像功能（默认根据环境变量）
        """
        self._client = httpx.Client(timeout=timeout)
        self._cache_hours = cache_hours

        # 镜像功能开关
        self._use_mirror = use_mirror if use_mirror is not None else V2EX_MIRROR_ENABLED

        # 镜像追踪器
        if self._use_mirror:
            self._mirror_tracker = MirrorTracker()
            logger.info(f"镜像功能已启用，追踪 {len(self.MIRRORS)} 个站点")
        else:
            self._mirror_tracker = None
            logger.info(f"镜像功能已禁用，使用单站点模式")

        # 关键词配置
        if custom_keywords:
            self.MONEY_KEYWORDS = custom_keywords.get('money_keywords', self.DEFAULT_MONEY_KEYWORDS)
            self.PAIN_KEYWORDS = custom_keywords.get('pain_keywords', self.DEFAULT_PAIN_KEYWORDS)
            self.DESPERATION_KEYWORDS = custom_keywords.get('desperation_keywords', self.DEFAULT_DESPERATION_KEYWORDS)
            self.TECH_KEYWORDS = custom_keywords.get('tech_keywords', self.DEFAULT_TECH_KEYWORDS)
        else:
            self.MONEY_KEYWORDS = self.DEFAULT_MONEY_KEYWORDS
            self.PAIN_KEYWORDS = self.DEFAULT_PAIN_KEYWORDS
            self.DESPERATION_KEYWORDS = self.DEFAULT_DESPERATION_KEYWORDS
            self.TECH_KEYWORDS = self.DEFAULT_TECH_KEYWORDS

        logger.info(f"V2EXRadar 初始化: cache={cache_hours}h, timeout={timeout}s, mirror={self._use_mirror}")

    def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            self._client.close()
            logger.info("V2EXRadar HTTP 客户端已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except:
            pass

    # ==========================================
    # 缓存管理
    # ==========================================

    def _get_cache_path(self, source: str) -> Path:
        """获取缓存文件路径"""
        return CACHE_DIR / f"v2ex_{source}.json"

    def _load_cache(self, source: str) -> Optional[List[Dict]]:
        """加载缓存数据"""
        cache_path = self._get_cache_path(source)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查缓存是否过期
            cache_time = datetime.datetime.fromisoformat(cache_data['timestamp'])
            now = datetime.datetime.now()

            if (now - cache_time).total_seconds() < self._cache_hours * 3600:
                logger.info(f"使用缓存数据: {source}, {len(cache_data['items'])} 条")
                return cache_data['items']

        except Exception as e:
            logger.warning(f"缓存加载失败: {source}, {e}")

        return None

    def _save_cache(self, source: str, items: List[Dict]):
        """保存缓存数据"""
        cache_path = self._get_cache_path(source)

        try:
            cache_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'source': source,
                'items': items,
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存已保存: {source}, {len(items)} 条")

        except Exception as e:
            logger.warning(f"缓存保存失败: {source}, {e}")

    # ==========================================
    # 数据获取
    # ==========================================

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        reraise=True,
    )
    def _fetch_rss(self, url: str) -> List[Dict]:
        """
        从 RSS Feed 获取数据（带重试）

        Args:
            url: RSS Feed URL

        Returns:
            解析后的帖子列表
        """
        logger.info(f"请求 RSS: {url}")

        response = self._client.get(url)
        response.raise_for_status()

        # 解析 XML
        root = ET.fromstring(response.content)
        items = []

        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            date_elem = item.find("pubDate")

            title = title_elem.text if title_elem is not None else ""
            link = link_elem.text if link_elem is not None else ""
            description = desc_elem.text if desc_elem is not None else ""
            pub_date = date_elem.text if date_elem is not None else ""

            items.append({
                'title': title,
                'url': link,
                'content': description,
                'pub_date': pub_date,
            })

        logger.info(f"RSS 解析成功: {len(items)} 条")
        return items

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        reraise=True,
    )
    def _fetch_api(self, url: str) -> List[Dict]:
        """
        从官方 API 获取数据（带重试）

        Args:
            url: API URL

        Returns:
            解析后的帖子列表
        """
        logger.info(f"请求 API: {url}")

        response = self._client.get(url)
        response.raise_for_status()

        data = response.json()
        items = []

        for topic in data:
            # API 返回格式
            title = topic.get('title', '')
            url = topic.get('url', '')
            content = topic.get('content', '') or topic.get('content_rendered', '')
            pub_date = topic.get('created', '')

            # 转换时间格式
            if isinstance(pub_date, int):
                pub_date = datetime.datetime.fromtimestamp(pub_date).strftime(
                    "%a, %d %b %Y %H:%M:%S +0800"
                )

            items.append({
                'title': title,
                'url': url,
                'content': content,
                'pub_date': pub_date,
            })

        logger.info(f"API 解析成功: {len(items)} 条")
        return items

    def _fetch_with_fallback(self, source: str) -> List[Dict]:
        """
        获取数据（带 fallback）

        优先尝试 RSS，失败则尝试 API。
        支持镜像站点切换。

        Args:
            source: 数据源名称

        Returns:
            帖子列表
        """
        # 如果启用镜像功能，使用镜像逻辑
        if self._use_mirror and self._mirror_tracker:
            return self._fetch_with_mirror_fallback(source)

        # 否则使用原有逻辑（单站点）
        return self._fetch_with_single_site(source)

    def _fetch_with_single_site(self, source: str) -> List[Dict]:
        """
        获取数据（单站点模式，兼容旧版）

        Args:
            source: 数据源名称

        Returns:
            帖子列表
        """
        # 先检查缓存
        cached = self._load_cache(source)
        if cached:
            return cached

        items = []

        # 尝试 RSS
        rss_url = self.RSS_FEEDS.get(source)
        if rss_url:
            try:
                items = self._fetch_rss(rss_url)
                if items:
                    self._save_cache(source, items)
                    return items
            except Exception as e:
                logger.warning(f"RSS 获取失败: {source}, {e}")

        # RSS 失败，尝试 API fallback
        api_url = self.API_ENDPOINTS.get('latest')  # 使用 latest 作为 fallback
        if api_url:
            try:
                items = self._fetch_api(api_url)
                if items:
                    self._save_cache(source, items)
                    return items
            except Exception as e:
                logger.warning(f"API fallback 失败: {source}, {e}")

        logger.error(f"所有数据源均失败: {source}")
        return []

    def _fetch_with_mirror_fallback(self, source: str) -> List[Dict]:
        """
        获取数据（带镜像 fallback）

        流程：
        1. 检查缓存
        2. 从最优镜像站点尝试
        3. 失败则依次尝试其他镜像
        4. 记录各站点响应时间

        Args:
            source: 数据源名称

        Returns:
            帖子列表
        """
        # 先检查缓存
        cached = self._load_cache(source)
        if cached:
            return cached

        # 获取排序后的镜像列表
        sorted_mirrors = self._mirror_tracker.get_sorted_mirrors(self.MIRRORS)

        for mirror in sorted_mirrors:
            # 跳过不健康站点
            if mirror.get('status') == MirrorStatus.UNHEALTHY:
                logger.debug(f"跳过不健康镜像: {mirror['name']}")
                continue

            try:
                start_time = time.time()
                items = self._fetch_from_mirror(mirror, source)
                response_time_ms = (time.time() - start_time) * 1000

                # 记录成功
                self._mirror_tracker.record_success(
                    mirror['name'],
                    mirror['base_url'],
                    response_time_ms,
                    mirror['priority'],
                    mirror['is_official']
                )

                if items:
                    self._save_cache(source, items)
                    logger.info(f"镜像 {mirror['name']} 成功: {len(items)} 条, {response_time_ms:.0f}ms")
                    return items

            except Exception as e:
                # 记录失败
                self._mirror_tracker.record_failure(
                    mirror['name'],
                    mirror['base_url'],
                    mirror['priority'],
                    mirror['is_official']
                )
                logger.warning(f"镜像 {mirror['name']} 失败: {e}")
                continue

        logger.error(f"所有镜像站点均失败: {source}")
        return []

    def _fetch_from_mirror(self, mirror: Dict, source: str) -> List[Dict]:
        """
        从指定镜像站点获取数据

        Args:
            mirror: 镜像配置
            source: 数据源名称

        Returns:
            帖子列表
        """
        base_url = mirror['base_url'].rstrip('/')

        # 尝试 RSS
        rss_path = self.RSS_PATHS.get(source)
        if rss_path:
            rss_url = f"{base_url}{rss_path}"
            try:
                items = self._fetch_rss(rss_url)
                if items:
                    return items
            except Exception as e:
                logger.debug(f"镜像 {mirror['name']} RSS 失败: {e}")

        # RSS 失败，尝试 API
        api_path = self.API_PATHS.get('latest')
        if api_path:
            api_url = f"{base_url}{api_path}"
            try:
                items = self._fetch_api(api_url)
                if items:
                    return items
            except Exception as e:
                logger.debug(f"镜像 {mirror['name']} API 失败: {e}")

        return []

    def get_mirror_stats(self) -> Dict:
        """
        获取镜像站点统计信息

        Returns:
            统计摘要
        """
        if self._mirror_tracker:
            return self._mirror_tracker.get_stats_summary()
        return {'total_mirrors': 0, 'mirrors': []}

    # ==========================================
    # 商机分析
    # ==========================================

    def fetch_leads(self, days: int = 1) -> List[Lead]:
        """
        获取商机线索

        Args:
            days: 筛选最近 N 天的帖子

        Returns:
            商机线索列表
        """
        logger.info(f"扫描 V2EX 商机（最近 {days} 天）...")
        all_leads = []

        for source in self.RSS_FEEDS.keys():
            items = self._fetch_with_fallback(source)

            for item in items:
                title = item['title']
                content = item['content']
                pub_date_str = item['pub_date']

                # 日期过滤
                try:
                    # 尝试多种日期格式
                    for fmt in [
                        "%a, %d %b %Y %H:%M:%S %z",
                        "%a, %d %b %Y %H:%M:%S +0800",
                        "%Y-%m-%d %H:%M:%S",
                    ]:
                        try:
                            pub_date = datetime.datetime.strptime(pub_date_str, fmt)
                            break
                        except ValueError:
                            continue

                    # 如果所有格式都失败，使用宽松匹配
                    if 'pub_date' not in locals():
                        # 从 URL 推断时间（V2EX 帖子 URL 包含 ID）
                        # 假设帖子是最近的
                        pub_date = datetime.datetime.now()

                    # 检查日期范围
                    now = datetime.datetime.now(datetime.timezone.utc) if pub_date.tzinfo else datetime.datetime.now()
                    pub_date_utc = pub_date.replace(tzinfo=datetime.timezone.utc) if not pub_date.tzinfo else pub_date

                    if (now - pub_date_utc).days > days:
                        continue

                except Exception as e:
                    logger.warning(f"日期解析失败: {pub_date_str}, {e}")
                    # 解析失败时保留帖子（假设是最近的）
                    pass

                # 分析内容
                tags, score = self._analyze_content(title, content)

                if tags:
                    lead = Lead(
                        source=f"V2EX-{source}",
                        title=title,
                        url=item['url'],
                        summary=self._clean_summary(content),
                        posted_date=pub_date_str,
                        tags=tags,
                        desperation_score=score,
                    )
                    all_leads.append(lead)

        # 按分数排序
        all_leads.sort(key=lambda x: x.desperation_score, reverse=True)

        logger.info(f"发现 {len(all_leads)} 个商机线索")
        return all_leads

    def _analyze_content(self, title: str, content: str) -> (List[str], int):
        """
        分析内容，提取标签和评分

        Args:
            title: 标题
            content: 内容

        Returns:
            (标签列表, 评分)
        """
        text = (title + " " + content).lower()
        found_tags = []
        score = 0

        # 检查付费关键词
        money_keywords_lower = [k.lower() for k in self.MONEY_KEYWORDS]
        if any(k in text for k in money_keywords_lower):
            found_tags.append("💰Money")
            score += 20

        # 检查痛点关键词
        pain_keywords_lower = [k.lower() for k in self.PAIN_KEYWORDS]
        if any(k in text for k in pain_keywords_lower):
            found_tags.append("🚑Pain")
            score += 10

        # 检查紧急程度关键词
        desperation_keywords_lower = [k.lower() for k in self.DESPERATION_KEYWORDS]
        if any(k in text for k in desperation_keywords_lower):
            found_tags.append("🔥Urgent")
            score += 100  # 高权重

        # 检查技术栈匹配
        tech_matches = [t for t in self.TECH_KEYWORDS if t.lower() in text]
        if tech_matches:
            found_tags.append(f"🛠️{','.join(tech_matches[:3])}")
            score += 30

        # 商机资格判断：需要 Money 或 Pain 或 Urgent
        if ("💰Money" in found_tags) or ("🚑Pain" in found_tags) or ("🔥Urgent" in found_tags):
            # 技术栈匹配加分
            if tech_matches:
                score += 50
            return found_tags, score

        return [], 0

    def _clean_summary(self, html_content: str) -> str:
        """清理 HTML 内容"""
        # 移除 HTML 标签
        clean = re.sub('<[^<]+?>', '', html_content)
        # 移除多余空白
        clean = re.sub(r'\s+', ' ', clean).strip()
        # 截断
        return clean[:200] + "..." if len(clean) > 200 else clean


# ==========================================
# 兼容旧版 API
# ==========================================

_radar_instance: Optional[V2EXRadar] = None


def get_radar() -> V2EXRadar:
    """获取全局 V2EXRadar 实例"""
    global _radar_instance
    if _radar_instance is None:
        _radar_instance = V2EXRadar()
    return _radar_instance


def fetch_v2ex_leads(days: int = 1, custom_keywords: dict = None) -> List[Dict]:
    """
    获取 V2EX 商机线索（兼容旧版 API）

    Args:
        days: 筛选最近 N 天
        custom_keywords: 自定义关键词

    Returns:
        商机线索字典列表
    """
    radar = V2EXRadar(custom_keywords=custom_keywords) if custom_keywords else get_radar()
    leads = radar.fetch_leads(days=days)
    return [lead.to_dict() for lead in leads]


# ==========================================
# CLI 入口
# ==========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="V2EX 商机雷达")
    parser.add_argument("--days", type=int, default=1, help="筛选最近 N 天")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    with V2EXRadar() as radar:
        leads = radar.fetch_leads(days=args.days)

        print(f"\n发现 {len(leads)} 个商机线索：")
        print("=" * 60)

        for lead in leads[:20]:  # 只显示前 20 个
            print(f"[Score: {lead.desperation_score}] {lead.tags}")
            print(f"  {lead.title}")
            print(f"  {lead.url}")
            print(f"  {lead.summary[:100]}...")
            print("-" * 40)