# -*- coding: utf-8 -*-
"""
自定义数据源采集器

支持用户自定义 RSS 源和网页源的采集。

功能：
- RSS 2.0 / Atom Feed 采集（使用 feedparser）
- 网页内容采集（使用 BeautifulSoup + lxml）
- 批量采集用户自定义数据源
- 失败自动重试
- 采集频率限制
"""

import httpx
import feedparser
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import logging
import time
import os
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

# 配置开关
def _parse_bool(val: str | None, default: bool = True) -> bool:
    """解析布尔值"""
    if val is None:
        return default
    return val.lower() in ('true', 'yes', '1', 'on', 'enabled')

CUSTOM_SOURCE_ENABLED = _parse_bool(os.getenv("CUSTOM_SOURCE_ENABLED"), True)


@dataclass
class CustomSourceItem:
    """自定义数据源条目"""
    source_name: str
    source_url: str
    title: str
    url: str
    content: str
    published_at: str = ""
    author: Optional[str] = None
    tags: List[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source_name": self.source_name,
            "source_url": self.source_url,
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "published_at": self.published_at,
            "author": self.author,
            "tags": self.tags or [],
        }


class CustomSourceSensor:
    """
    自定义数据源采集器

    支持：
    - RSS/Atom Feed 采集
    - 网页内容采集（CSS 选择器）
    - 批量采集用户自定义数据源
    """

    # 默认限制
    DEFAULT_MAX_ITEMS = 50
    DEFAULT_TIMEOUT = 15.0
    DEFAULT_CONTENT_TRUNCATE = 500

    def __init__(
        self,
        timeout: float = None,
        max_items: int = None,
        content_truncate: int = None,
    ):
        """
        初始化采集器

        Args:
            timeout: HTTP 请求超时时间（秒）
            max_items: 单源最大条目数
            content_truncate: 内容截断长度
        """
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._max_items = max_items or self.DEFAULT_MAX_ITEMS
        self._content_truncate = content_truncate or self.DEFAULT_CONTENT_TRUNCATE
        self._client: Optional[httpx.Client] = None

        logger.info(f"CustomSourceSensor 初始化: timeout={self._timeout}s, max_items={self._max_items}")

    def _get_client(self) -> httpx.Client:
        """获取 HTTP 客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            self._client.close()
            self._client = None
            logger.debug("CustomSourceSensor HTTP 客户端已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ==========================================
    # RSS 采集
    # ==========================================

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        reraise=True,
    )
    def fetch_rss(self, source_name: str, url: str) -> List[CustomSourceItem]:
        """
        采集 RSS/Atom Feed

        使用 feedparser 库，自动识别 RSS 2.0 / Atom 格式。

        Args:
            source_name: 数据源名称
            url: RSS Feed URL

        Returns:
            条目列表
        """
        if not CUSTOM_SOURCE_ENABLED:
            logger.warning("自定义数据源功能已禁用")
            return []

        logger.info(f"采集 RSS: {source_name} - {url}")

        try:
            client = self._get_client()
            response = client.get(url)
            response.raise_for_status()

            # 使用 feedparser 解析
            feed = feedparser.parse(response.content)

            # 检查解析错误
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS 解析警告: {source_name}, {feed.bozo_exception}")

            items = []
            for entry in feed.entries[:self._max_items]:
                # 提取内容
                content = ""
                if 'summary' in entry:
                    content = entry.summary
                elif 'content' in entry and entry.content:
                    content = entry.content[0].get('value', '')

                # 清理 HTML 标签
                content = self._clean_html(content)

                # 截断内容
                content = self._truncate_content(content)

                item = CustomSourceItem(
                    source_name=source_name,
                    source_url=url,
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    content=content,
                    published_at=entry.get('published') or entry.get('updated', ''),
                    author=entry.get('author', None),
                )
                items.append(item)

            logger.info(f"RSS 采集完成: {source_name}, {len(items)} 条")
            return items

        except Exception as e:
            logger.error(f"RSS 采集失败: {source_name}, {e}")
            raise

    # ==========================================
    # 网页采集
    # ==========================================

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        reraise=True,
    )
    def fetch_webpage(
        self,
        source_name: str,
        url: str,
        selectors: Dict[str, str] = None,
    ) -> List[CustomSourceItem]:
        """
        采集网页内容（使用 CSS 选择器）

        Args:
            source_name: 数据源名称
            url: 网页 URL
            selectors: CSS 选择器配置
                - item: 条目容器选择器（必需）
                - title: 标题选择器
                - link: 链接选择器
                - content: 内容选择器

        Returns:
            条目列表
        """
        if not CUSTOM_SOURCE_ENABLED:
            logger.warning("自定义数据源功能已禁用")
            return []

        logger.info(f"采集网页: {source_name} - {url}")

        # 默认选择器
        default_selectors = {
            'item': 'article',
            'title': 'h1, h2, h3',
            'link': 'a',
            'content': 'p',
        }
        selectors = {**default_selectors, **(selectors or {})}

        try:
            client = self._get_client()
            response = client.get(url)
            response.raise_for_status()

            # 使用 lxml 解析器（更快）
            soup = BeautifulSoup(response.content, 'lxml')

            items = []
            item_selector = selectors.get('item', 'article')

            for item_elem in soup.select(item_selector)[:self._max_items]:
                title = self._extract_text(item_elem, selectors.get('title', 'h1,h2,h3'))
                link = self._extract_link(item_elem, selectors.get('link', 'a'), url)
                content = self._extract_text(item_elem, selectors.get('content', 'p'))

                # 截断内容
                content = self._truncate_content(content)

                if title and link:
                    item = CustomSourceItem(
                        source_name=source_name,
                        source_url=url,
                        title=title,
                        url=link,
                        content=content,
                    )
                    items.append(item)

            logger.info(f"网页采集完成: {source_name}, {len(items)} 条")
            return items

        except Exception as e:
            logger.error(f"网页采集失败: {source_name}, {e}")
            raise

    # ==========================================
    # 批量采集
    # ==========================================

    def fetch_user_sources(
        self,
        user_id: int,
        tool_type: str,
        delay: float = 1.0,
    ) -> List[CustomSourceItem]:
        """
        采集用户所有自定义数据源

        Args:
            user_id: 用户 ID
            tool_type: 工具类型（mission / alpha / bounty）
            delay: 请求间隔（秒），避免触发反爬

        Returns:
            所有条目列表
        """
        if not CUSTOM_SOURCE_ENABLED:
            logger.warning("自定义数据源功能已禁用")
            return []

        from src.config_loader import get_user_sources

        sources = get_user_sources(user_id, tool_type)

        if not sources:
            logger.info(f"用户无自定义数据源: user_id={user_id}, tool_type={tool_type}")
            return []

        logger.info(f"开始采集用户数据源: user_id={user_id}, count={len(sources)}")

        all_items = []

        for i, source in enumerate(sources):
            # 请求间隔
            if i > 0 and delay > 0:
                time.sleep(delay)

            source_type = source.get('source_type', 'rss')

            try:
                if source_type == 'rss':
                    items = self.fetch_rss(
                        source['name'],
                        source['url']
                    )
                    all_items.extend(items)

                elif source_type == 'webpage':
                    # 解析选择器配置
                    config = source.get('config', {})
                    if isinstance(config, str):
                        import json
                        try:
                            config = json.loads(config)
                        except:
                            config = {}

                    selectors = config.get('selectors', {})

                    items = self.fetch_webpage(
                        source['name'],
                        source['url'],
                        selectors
                    )
                    all_items.extend(items)

            except Exception as e:
                logger.warning(f"数据源采集失败: {source['name']}, {e}")
                continue

        logger.info(f"用户数据源采集完成: user_id={user_id}, total={len(all_items)}")
        return all_items

    def fetch_sources(
        self,
        sources: List[Dict],
        delay: float = 1.0,
    ) -> List[CustomSourceItem]:
        """
        批量采集数据源列表

        Args:
            sources: 数据源配置列表
                - name: 数据源名称
                - url: URL
                - source_type: 类型（rss / webpage）
                - config: 可选配置（JSON）
            delay: 请求间隔（秒）

        Returns:
            所有条目列表
        """
        if not CUSTOM_SOURCE_ENABLED:
            logger.warning("自定义数据源功能已禁用")
            return []

        all_items = []

        for i, source in enumerate(sources):
            if i > 0 and delay > 0:
                time.sleep(delay)

            source_type = source.get('source_type', 'rss')

            try:
                if source_type == 'rss':
                    items = self.fetch_rss(
                        source['name'],
                        source['url']
                    )
                    all_items.extend(items)

                elif source_type == 'webpage':
                    config = source.get('config', {})
                    if isinstance(config, str):
                        import json
                        try:
                            config = json.loads(config)
                        except:
                            config = {}

                    selectors = config.get('selectors', {})

                    items = self.fetch_webpage(
                        source['name'],
                        source['url'],
                        selectors
                    )
                    all_items.extend(items)

            except Exception as e:
                logger.warning(f"数据源采集失败: {source.get('name', 'unknown')}, {e}")
                continue

        return all_items

    # ==========================================
    # 辅助方法
    # ==========================================

    def _extract_text(self, parent, selector: str) -> str:
        """从元素中提取文本"""
        if not parent or not selector:
            return ""

        try:
            elem = parent.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        except Exception:
            pass

        return ""

    def _extract_link(self, parent, selector: str, base_url: str) -> str:
        """从元素中提取链接（处理相对链接）"""
        if not parent or not selector:
            return ""

        try:
            elem = parent.select_one(selector)
            if elem and elem.get('href'):
                link = elem['href']
                # 处理相对链接
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)
                return link
        except Exception:
            pass

        return ""

    def _clean_html(self, html_content: str) -> str:
        """清理 HTML 内容"""
        if not html_content:
            return ""

        # 使用 BeautifulSoup 清理
        soup = BeautifulSoup(html_content, 'lxml')
        return soup.get_text(separator=' ', strip=True)

    def _truncate_content(self, content: str) -> str:
        """截断内容"""
        if not content:
            return ""

        if len(content) > self._content_truncate:
            return content[:self._content_truncate] + "..."

        return content


# ==========================================
# 便捷函数
# ==========================================

def fetch_custom_rss(name: str, url: str) -> List[Dict]:
    """
    采集单个 RSS 源（便捷函数）

    Args:
        name: 数据源名称
        url: RSS URL

    Returns:
        条目字典列表
    """
    with CustomSourceSensor() as sensor:
        items = sensor.fetch_rss(name, url)
        return [item.to_dict() for item in items]


def fetch_custom_webpage(name: str, url: str, selectors: Dict = None) -> List[Dict]:
    """
    采集单个网页源（便捷函数）

    Args:
        name: 数据源名称
        url: 网页 URL
        selectors: CSS 选择器

    Returns:
        条目字典列表
    """
    with CustomSourceSensor() as sensor:
        items = sensor.fetch_webpage(name, url, selectors)
        return [item.to_dict() for item in items]


def fetch_user_custom_sources(user_id: int, tool_type: str) -> List[Dict]:
    """
    采集用户自定义数据源（便捷函数）

    Args:
        user_id: 用户 ID
        tool_type: 工具类型

    Returns:
        条目字典列表
    """
    with CustomSourceSensor() as sensor:
        items = sensor.fetch_user_sources(user_id, tool_type)
        return [item.to_dict() for item in items]


# ==========================================
# CLI 入口
# ==========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="自定义数据源采集器")
    parser.add_argument("--rss", type=str, help="RSS URL")
    parser.add_argument("--webpage", type=str, help="网页 URL")
    parser.add_argument("--name", type=str, default="测试", help="数据源名称")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    with CustomSourceSensor() as sensor:
        if args.rss:
            items = sensor.fetch_rss(args.name, args.rss)
            print(f"\nRSS 采集结果: {len(items)} 条")
            for item in items[:5]:
                print(f"  - {item.title}")

        elif args.webpage:
            items = sensor.fetch_webpage(args.name, args.webpage)
            print(f"\n网页采集结果: {len(items)} 条")
            for item in items[:5]:
                print(f"  - {item.title}")

        else:
            print("请指定 --rss 或 --webpage 参数")