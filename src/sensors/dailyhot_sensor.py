# -*- coding: utf-8 -*-
"""
DailyHotApi Sensor - 热榜数据源传感器

从 DailyHotApi 实例获取各平台热榜数据，支持分类筛选。
DailyHotApi 是一个开源的热榜聚合 API，支持知乎、微博、B站等 60+ 平台。

项目地址: https://github.com/DailyHot/DailyHotApi
"""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

from src.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 分类与子平台的映射关系
# ─────────────────────────────────────────────────────────────

CATEGORY_MAP: Dict[str, Dict[str, Any]] = {
    "tech": {
        "label": "科技数字",
        "platforms": [
            {"key": "sspai", "name": "少数派"},
            {"key": "ithome", "name": "IT之家"},
            {"key": "ifanr", "name": "爱范儿"},
            {"key": "huxiu", "name": "虎嗅"},
        ]
    },
    "dev": {
        "label": "开发者",
        "platforms": [
            {"key": "juejin", "name": "稀土掘金"},
            {"key": "v2ex", "name": "V2EX"},
            {"key": "hellogithub", "name": "HelloGitHub"},
            {"key": "csdn", "name": "CSDN"},
            {"key": "51cto", "name": "51CTO"},
        ]
    },
    "news": {
        "label": "综合资讯",
        "platforms": [
            {"key": "zhihu", "name": "知乎"},
            {"key": "toutiao", "name": "今日头条"},
            {"key": "thepaper", "name": "澎湃新闻"},
            {"key": "qq-news", "name": "腾讯新闻"},
        ]
    },
    "entertainment": {
        "label": "内容娱乐",
        "platforms": [
            {"key": "bilibili", "name": "哔哩哔哩"},
            {"key": "douban-movie", "name": "豆瓣电影"},
        ]
    },
}

# 所有可用平台列表（用于测试连接）
ALL_PLATFORMS = []
for cat_data in CATEGORY_MAP.values():
    ALL_PLATFORMS.extend(cat_data["platforms"])


@dataclass
class HotItem:
    """热榜条目数据结构"""
    title: str
    url: str
    hot: int
    timestamp: int
    source: str
    source_key: str
    category: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "hot": self.hot,
            "timestamp": self.timestamp,
            "source": self.source,
            "source_key": self.source_key,
            "category": self.category,
        }


class DailyHotSensor:
    """
    DailyHotApi 传感器

    从 DailyHotApi 实例获取热榜数据，支持：
    - 按分类获取多个平台数据
    - 单平台数据获取
    - 连接测试
    """

    def __init__(self, timeout: int = 15):
        """
        初始化传感器

        Args:
            timeout: 请求超时时间（秒）
        """
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        """获取 DailyHotApi 实例地址"""
        return settings.DAILYHOT_API_URL

    def fetch_platform(
        self,
        platform_key: str,
        limit: int = 20,
        category: str = None,
    ) -> List[HotItem]:
        """
        获取单个平台的热榜数据

        Args:
            platform_key: 平台标识，如 "zhihu", "bilibili"
            limit: 返回条目数量限制
            category: 所属分类（用于标记数据）

        Returns:
            热榜条目列表，失败时返回空列表
        """
        url = f"{self.base_url}/{platform_key}"
        items = []

        try:
            resp = httpx.get(url, timeout=self._timeout, follow_redirects=True)

            if resp.status_code != 200:
                logger.warning(f"DailyHotApi 请求失败: {url}, status={resp.status_code}")
                return []

            data = resp.json()

            # DailyHotApi 返回格式: { "code": 200, "message": "...", "data": [...] }
            if isinstance(data, dict):
                if data.get("code") != 200:
                    logger.warning(f"DailyHotApi 返回错误: {data.get('message', 'unknown')}")
                    return []
                data = data.get("data", [])

            if not isinstance(data, list):
                logger.warning(f"DailyHotApi 返回格式异常: {type(data)}")
                return []

            # 获取平台名称
            platform_name = self._get_platform_name(platform_key)

            # 解析数据
            for item in data[:limit]:
                try:
                    hot_item = self._parse_item(item, platform_key, platform_name, category)
                    if hot_item:
                        items.append(hot_item)
                except Exception as e:
                    logger.debug(f"解析条目失败: {e}")
                    continue

            logger.info(f"DailyHotApi 获取成功: {platform_key} ({len(items)} 条)")

        except httpx.TimeoutException:
            logger.warning(f"DailyHotApi 请求超时: {url}")
        except httpx.RequestError as e:
            logger.warning(f"DailyHotApi 请求错误: {e}")
        except Exception as e:
            logger.error(f"DailyHotApi 未知错误: {e}")

        return items

    def fetch_by_categories(
        self,
        categories: List[str],
        limit_per_platform: int = 10,
    ) -> List[HotItem]:
        """
        按分类标签并发获取多个平台数据

        Args:
            categories: 分类列表，如 ["tech", "dev"]
            limit_per_platform: 每个平台返回的条目数量

        Returns:
            合并后的热榜条目列表
        """
        if not categories:
            categories = ["tech", "dev"]  # 默认分类

        all_items = []
        platforms_to_fetch = []

        # 收集需要获取的平台
        for category in categories:
            if category not in CATEGORY_MAP:
                logger.warning(f"未知分类: {category}")
                continue

            cat_data = CATEGORY_MAP[category]
            for platform in cat_data["platforms"]:
                platforms_to_fetch.append({
                    "key": platform["key"],
                    "category": category,
                })

        if not platforms_to_fetch:
            return []

        logger.info(f"DailyHotApi 开始获取 {len(platforms_to_fetch)} 个平台数据...")

        # 并发获取
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for p in platforms_to_fetch:
                future = executor.submit(
                    self.fetch_platform,
                    p["key"],
                    limit_per_platform,
                    p["category"],
                )
                futures[future] = p["key"]

            for future in as_completed(futures):
                platform_key = futures[future]
                try:
                    items = future.result()
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"获取 {platform_key} 失败: {e}")

        # 按热度排序
        all_items.sort(key=lambda x: x.hot, reverse=True)

        logger.info(f"DailyHotApi 共获取 {len(all_items)} 条数据")
        return all_items

    def test_connection(self) -> Dict[str, bool]:
        """
        测试各平台连接状态

        Returns:
            平台连接状态字典 {platform_key: bool}
        """
        results = {}

        # 只测试部分代表性平台
        test_platforms = ["zhihu", "bilibili", "juejin", "sspai"]

        for platform in test_platforms:
            try:
                url = f"{self.base_url}/{platform}"
                resp = httpx.get(url, timeout=10, follow_redirects=True)
                results[platform] = resp.status_code == 200
            except Exception:
                results[platform] = False

        return results

    def get_category_map(self) -> Dict[str, Dict[str, Any]]:
        """
        获取分类映射关系（供前端展示用）

        Returns:
            分类映射字典
        """
        return CATEGORY_MAP

    def _parse_item(
        self,
        item: Dict[str, Any],
        platform_key: str,
        platform_name: str,
        category: str,
    ) -> Optional[HotItem]:
        """
        解析单个热榜条目

        DailyHotApi 不同平台返回格式略有不同，这里做统一处理
        """
        # 标题
        title = item.get("title") or item.get("name", "")
        if not title:
            return None

        # 链接
        url = item.get("url") or item.get("link", "")
        if not url:
            # 某些平台可能没有外部链接
            url = ""

        # 热度值
        hot = 0
        hot_data = item.get("hot") or item.get("extra", {}).get("hot", 0)
        if isinstance(hot_data, (int, float)):
            hot = int(hot_data)
        elif isinstance(hot_data, str):
            # 处理 "123万" 这样的格式
            try:
                if "万" in hot_data:
                    hot = int(float(hot_data.replace("万", "")) * 10000)
                elif "亿" in hot_data:
                    hot = int(float(hot_data.replace("亿", "")) * 100000000)
                else:
                    hot = int(hot_data.replace(",", ""))
            except (ValueError, AttributeError):
                pass

        # 时间戳
        timestamp = 0
        ts_data = item.get("timestamp") or item.get("extra", {}).get("timestamp", 0)
        if isinstance(ts_data, (int, float)):
            # DailyHotApi 返回的是秒级时间戳，转换为毫秒
            timestamp = int(ts_data) * 1000 if ts_data < 10000000000 else int(ts_data)

        return HotItem(
            title=title,
            url=url,
            hot=hot,
            timestamp=timestamp,
            source=platform_name,
            source_key=platform_key,
            category=category or "",
        )

    def _get_platform_name(self, platform_key: str) -> str:
        """根据平台 key 获取中文名称"""
        for cat_data in CATEGORY_MAP.values():
            for platform in cat_data["platforms"]:
                if platform["key"] == platform_key:
                    return platform["name"]
        return platform_key


# ─────────────────────────────────────────────────────────────
# 便捷函数
# ─────────────────────────────────────────────────────────────

def fetch_dailyhot(categories: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取热榜数据的便捷函数

    Args:
        categories: 分类列表，默认 ["tech", "dev"]
        limit: 每个平台的条目数量

    Returns:
        热榜数据列表（字典格式）
    """
    sensor = DailyHotSensor()
    if categories is None:
        categories = ["tech", "dev"]

    items = sensor.fetch_by_categories(categories, limit)
    return [item.to_dict() for item in items]


def test_dailyhot_connection() -> Dict[str, bool]:
    """
    测试 DailyHotApi 连接的便捷函数
    """
    sensor = DailyHotSensor()
    return sensor.test_connection()


# ─────────────────────────────────────────────────────────────
# CLI 测试入口
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  DailyHotApi Sensor 测试")
    print("=" * 60)
    print(f"\nAPI 地址: {settings.DAILYHOT_API_URL}")
    print(f"配置地址: {settings.DAILYHOT_API_URL}")
    print()

    # 测试连接
    print("测试连接...")
    results = test_dailyhot_connection()
    for platform, status in results.items():
        icon = "✓" if status else "✗"
        print(f"  {icon} {platform}")
    print()

    # 获取数据
    categories = sys.argv[1:] if len(sys.argv) > 1 else ["tech", "dev"]
    print(f"获取分类: {categories}")
    print("-" * 60)

    items = fetch_dailyhot(categories, limit=5)

    for i, item in enumerate(items[:20], 1):
        print(f"{i}. [{item['source']}] {item['title']}")
        print(f"   热度: {item['hot']:,} | 链接: {item['url'][:50]}...")
        print()

    print(f"共 {len(items)} 条数据")