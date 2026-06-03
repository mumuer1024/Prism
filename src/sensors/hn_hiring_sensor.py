# -*- coding: utf-8 -*-
"""
Hacker News "Who is hiring" 传感器

功能：
- 抓取 HN 每月 "Ask HN: Who is hiring?" 月帖
- 解析招聘评论，提取标准化数据
- 返回科技/AI 行业相关招聘机会
"""

import httpx
import re
import datetime
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = Path(__file__).parent.parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


@dataclass
class HNHiringOpportunity:
    """HN 招聘机会数据结构"""
    company: str
    position: str
    location: str
    description: str
    tags: List[str] = field(default_factory=list)
    url: Optional[str] = None
    comment_id: Optional[int] = None
    source_post_id: Optional[int] = None
    source_post_title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "company": self.company,
            "position": self.position,
            "location": self.location,
            "description": self.description,
            "tags": self.tags,
            "url": self.url,
            "comment_id": self.comment_id,
            "source_post_id": self.source_post_id,
            "source_post_title": self.source_post_title,
        }


class HNHiringSensor:
    """
    Hacker News "Who is hiring" 传感器

    抓取每月招聘帖，解析评论中的招聘信息。

    API 来源：
    - Algolia HN Search API: https://hn.algolia.com/api/v1/search
    - HN Firebase API: https://hacker-news.firebaseio.com/v0/item/{id}.json
    """

    # Algolia 搜索 API
    ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

    # HN Firebase API
    HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

    # 搜索关键词
    SEARCH_QUERY = "Ask HN: Who is hiring"

    # 科技/AI 相关关键词（用于筛选）
    TECH_KEYWORDS = [
        "AI", "ML", "machine learning", "artificial intelligence",
        "LLM", "GPT", "OpenAI", "Claude", "deep learning",
        "Python", "Rust", "Go", "TypeScript", "JavaScript",
        "React", "Vue", "Node", "Next.js",
        "Web3", "blockchain", "crypto", "Solana",
        "backend", "frontend", "fullstack", "devops",
        "remote", "senior", "junior", "intern",
        "SaaS", "startup", "YC", "Series A", "Series B",
    ]

    # 排除关键词（非招聘或非科技）
    EXCLUDE_KEYWORDS = [
        "marketing", "sales", "HR", "recruiter", "agency",
        "non-tech", "fashion", "food", "restaurant",
    ]

    # 缓存有效期（小时）
    CACHE_HOURS = 6

    def __init__(self, timeout: float = 15.0, cache_hours: int = 6):
        """
        初始化传感器

        Args:
            timeout: HTTP 请求超时时间
            cache_hours: 缓存有效期（小时）
        """
        self._client = httpx.Client(timeout=timeout)
        self._cache_hours = cache_hours
        logger.info(f"HNHiringSensor 初始化: timeout={timeout}s, cache={cache_hours}h")

    def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            self._client.close()
            logger.info("HNHiringSensor HTTP 客户端已关闭")

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

    def _get_cache_path(self) -> Path:
        """获取缓存文件路径"""
        # 缓存文件名包含月份，每月更新一次
        month_str = datetime.datetime.now().strftime("%Y-%m")
        return CACHE_DIR / f"hn_hiring_{month_str}.json"

    def _load_cache(self) -> Optional[List[Dict]]:
        """加载缓存数据"""
        cache_path = self._get_cache_path()

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查缓存是否过期
            cache_time = datetime.datetime.fromisoformat(cache_data['timestamp'])
            now = datetime.datetime.now()

            if (now - cache_time).total_seconds() < self._cache_hours * 3600:
                logger.info(f"使用缓存数据: {len(cache_data['opportunities'])} 条")
                return cache_data['opportunities']

        except Exception as e:
            logger.warning(f"缓存加载失败: {e}")

        return None

    def _save_cache(self, opportunities: List[Dict]):
        """保存缓存数据"""
        cache_path = self._get_cache_path()

        try:
            cache_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'opportunities': opportunities,
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存已保存: {len(opportunities)} 条")

        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    # ==========================================
    # 数据获取
    # ==========================================

    def _search_hiring_posts(self) -> Optional[Dict]:
        """
        搜索最新的 "Who is hiring" 帖子

        Returns:
            帖子数据（包含 ID、标题等）
        """
        try:
            # 使用 Algolia 搜索 API
            params = {
                "query": self.SEARCH_QUERY,
                "tags": "story",  # 只搜索帖子（不搜索评论）
                "hitsPerPage": 5,  # 只取最近几期
            }

            response = self._client.get(self.ALGOLIA_SEARCH_URL, params=params)
            response.raise_for_status()

            data = response.json()
            hits = data.get('hits', [])

            if not hits:
                logger.warning("未找到 'Who is hiring' 帖子")
                return None

            # 找到最新一期（标题格式: "Ask HN: Who is hiring? (Month Year)"）
            for hit in hits:
                title = hit.get('title', '')
                if title and "Who is hiring" in title:
                    logger.info(f"找到招聘帖: {title}")
                    return {
                        'id': hit.get('objectID'),
                        'title': title,
                        'points': hit.get('points', 0),
                        'author': hit.get('author', 'unknown'),
                        'created_at': hit.get('created_at'),
                    }

            return None

        except Exception as e:
            logger.error(f"搜索招聘帖失败: {e}")
            return None

    def _fetch_post_comments(self, post_id: int) -> List[Dict]:
        """
        获取帖子的评论列表

        Args:
            post_id: 帖子 ID

        Returns:
            评论列表
        """
        try:
            # 获取帖子详情
            post_url = self.HN_ITEM_URL.format(id=post_id)
            response = self._client.get(post_url)
            response.raise_for_status()

            post_data = response.json()

            if not post_data:
                logger.warning(f"帖子 {post_id} 无数据")
                return []

            # 获取评论 ID 列表
            kids = post_data.get('kids', [])

            if not kids:
                logger.warning(f"帖子 {post_id} 无评论")
                return []

            # 只取前 200 条评论（招聘帖通常有大量评论）
            comment_ids = kids[:200]

            comments = []
            for cid in comment_ids:
                try:
                    comment_url = self.HN_ITEM_URL.format(id=cid)
                    resp = self._client.get(comment_url)
                    resp.raise_for_status()

                    comment_data = resp.json()

                    if comment_data and comment_data.get('text'):
                        comments.append({
                            'id': cid,
                            'text': comment_data.get('text', ''),
                            'by': comment_data.get('by', 'unknown'),
                        })

                except Exception as e:
                    logger.debug(f"获取评论 {cid} 失败: {e}")
                    continue

            logger.info(f"获取到 {len(comments)} 条评论")
            return comments

        except Exception as e:
            logger.error(f"获取帖子评论失败: {e}")
            return []

    def _parse_comment(self, comment: Dict, post_id: int, post_title: str) -> Optional[HNHiringOpportunity]:
        """
        解析单条评论，提取招聘信息

        Args:
            comment: 评论数据
            post_id: 原帖 ID
            post_title: 原帖标题

        Returns:
            HNHiringOpportunity 或 None
        """
        text = comment.get('text', '')
        comment_id = comment.get('id')

        # 清理 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)

        # 招聘评论通常以公司名开头，格式多样：
        # "| Company Name | Position | Location | ..."
        # "Company Name - Position - Location"
        # "Company: X | Role: Y | Location: Z"

        # 常见分隔符
        lines = text.strip().split('\n')
        first_line = lines[0] if lines else ""

        # 尝试解析公司名和职位
        company = None
        position = None
        location = None

        # 格式 1: | Company | Position | Location |
        if '|' in first_line:
            parts = [p.strip() for p in first_line.split('|') if p.strip()]
            if len(parts) >= 2:
                company = parts[0]
                position = parts[1] if len(parts) > 1 else ""
                location = parts[2] if len(parts) > 2 else ""

        # 格式 2: Company - Position - Location
        elif ' - ' in first_line:
            parts = [p.strip() for p in first_line.split(' - ') if p.strip()]
            if len(parts) >= 2:
                company = parts[0]
                position = parts[1] if len(parts) > 1 else ""
                location = parts[2] if len(parts) > 2 else ""

        # 格式 3: Company: X | Role: Y
        elif ':' in first_line:
            # 尝试提取关键字段
            company_match = re.search(r'Company[：:]\s*([^\|,\n]+)', text, re.IGNORECASE)
            position_match = re.search(r'(Position|Role|Job|Title)[：:]\s*([^\|,\n]+)', text, re.IGNORECASE)
            location_match = re.search(r'(Location|Loc|Remote|Based)[：:]\s*([^\|,\n]+)', text, re.IGNORECASE)

            if company_match:
                company = company_match.group(1).strip()
            if position_match:
                position = position_match.group(2).strip()
            if location_match:
                location = location_match.group(2).strip()

        # 格式 4: 简单的公司名 + 描述
        if not company:
            # 查找首行大写字母开头的词（可能是公司名）
            first_word = first_line.split()[0] if first_line.split() else ""
            if first_word and first_word[0].isupper() and len(first_word) > 2:
                company = first_word
                # 其余部分作为职位描述
                remaining = first_line[len(first_word):].strip()
                if remaining.startswith('-') or remaining.startswith('|'):
                    remaining = remaining[1:].strip()
                position = remaining[:50] if remaining else ""

        # 如果无法解析出公司名，跳过
        if not company:
            return None

        # 提取 URL（如果有）
        url_match = re.search(r'https?://[^\s<>"]+', text)
        url = url_match.group(0) if url_match else None

        # 提取标签（科技相关关键词）
        tags = []
        for kw in self.TECH_KEYWORDS:
            if kw.lower() in text.lower():
                tags.append(kw)

        # 过滤排除关键词
        for kw in self.EXCLUDE_KEYWORDS:
            if kw.lower() in text.lower():
                return None

        # 构建描述（取前 200 字符）
        description = text[:200].strip()

        return HNHiringOpportunity(
            company=company[:50],  # 限制长度
            position=position[:100] if position else "Various positions",
            location=location[:50] if location else "Remote/On-site",
            description=description,
            tags=tags[:10],  # 最多 10 个标签
            url=url,
            comment_id=comment_id,
            source_post_id=post_id,
            source_post_title=post_title,
        )

    # ==========================================
    # 公共接口
    # ==========================================

    def fetch_opportunities(self, limit: int = 50) -> List[HNHiringOpportunity]:
        """
        获取招聘机会

        Args:
            limit: 返回数量限制

        Returns:
            招聘机会列表
        """
        # 检查缓存
        cached = self._load_cache()
        if cached:
            return [HNHiringOpportunity(**op) for op in cached[:limit]]

        # 搜索最新招聘帖
        post_info = self._search_hiring_posts()

        if not post_info:
            logger.warning("未找到招聘帖")
            return []

        post_id = int(post_info['id'])
        post_title = post_info['title']

        # 获取评论
        comments = self._fetch_post_comments(post_id)

        if not comments:
            logger.warning("未获取到评论")
            return []

        # 解析评论
        opportunities = []
        for comment in comments:
            opp = self._parse_comment(comment, post_id, post_title)
            if opp:
                opportunities.append(opp)

        logger.info(f"解析到 {len(opportunities)} 个招聘机会")

        # 缓存
        self._save_cache([opp.to_dict() for opp in opportunities])

        return opportunities[:limit]

    def get_hiring_post_info(self) -> Optional[Dict]:
        """
        获取最新招聘帖信息（不解析评论）

        Returns:
            帖子基本信息
        """
        return self._search_hiring_posts()


# ============================================================================
# 独立运行入口
# ============================================================================

if __name__ == "__main__":
    import sys

    # Ensure UTF-8 output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("  HN WHO IS HIRING SENSOR")
    print("=" * 60)

    with HNHiringSensor() as sensor:
        # 先显示帖子信息
        post_info = sensor.get_hiring_post_info()
        if post_info:
            print(f"\n📅 最新招聘帖: {post_info['title']}")
            print(f"   作者: {post_info['author']}")
            print(f"   分数: {post_info['points']}")
            print(f"   ID: {post_info['id']}")

        # 获取招聘机会
        print("\n🔍 正在解析招聘机会...")
        opportunities = sensor.fetch_opportunities(limit=20)

        print(f"\n找到 {len(opportunities)} 个招聘机会:\n")

        for i, opp in enumerate(opportunities, 1):
            print(f"{i}. {opp.company}")
            print(f"   职位: {opp.position}")
            print(f"   地点: {opp.location}")
            print(f"   标签: {', '.join(opp.tags[:5])}")
            if opp.url:
                print(f"   链接: {opp.url}")
            print()