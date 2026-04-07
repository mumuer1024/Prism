# -*- coding: utf-8 -*-
"""
数据源健康检测模块

检测各数据源的可用性和响应时间。

功能：
- 定期检测各数据源可用性
- 响应时间记录
- 连续失败计数
- 健康状态判定
- API 端点支持
"""

import httpx
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"      # 健康
    DEGRADED = "degraded"    # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    UNKNOWN = "unknown"      # 未检测
    NOT_CONFIGURED = "not_configured"  # 未配置


@dataclass
class SourceHealthResult:
    """数据源健康检测结果"""
    source_name: str
    source_type: str  # rss / api / webpage
    url: str
    is_healthy: bool
    status: HealthStatus
    response_time_ms: float
    last_check_at: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "url": self.url,
            "is_healthy": self.is_healthy,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "last_check_at": self.last_check_at.isoformat(),
            "error_message": self.error_message,
            "consecutive_failures": self.consecutive_failures,
        }


class SourceHealthChecker:
    """
    数据源健康检测器

    定期检测各数据源的可用性。
    """

    # 内置数据源列表
    BUILTIN_SOURCES = [
        {"name": "Hacker News", "type": "api", "url": "https://hacker-news.firebaseio.com/v3/topstories.json", "is_public": True},
        {"name": "GitHub Trending", "type": "api", "url": "https://api.github.com/graphql", "requires_auth": True},
        {"name": "V2EX RSS", "type": "rss", "url": "https://www.v2ex.com/index.xml"},
        {"name": "V2EX API", "type": "api", "url": "https://www.v2ex.com/api/topics/hot.json", "is_public": True},
        {"name": "ArXiv AI", "type": "rss", "url": "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"},
        {"name": "Product Hunt", "type": "api", "url": "https://api.producthunt.com/v2/api/graphql", "requires_auth": True},
        {"name": "36Kr", "type": "rss", "url": "https://36kr.com/feed"},
        {"name": "WallStreetCN", "type": "rss", "url": "https://wallstreetcn.com/feed"},
    ]

    # 状态判定阈值
    RESPONSE_TIME_DEGRADED_MS = 5000    # 降级阈值
    RESPONSE_TIME_UNHEALTHY_MS = 10000  # 不健康阈值
    CONSECUTIVE_FAILURES_THRESHOLD = 3  # 连续失败阈值
    CHECK_TIMEOUT = 10.0                # 检测超时

    def __init__(self, timeout: float = None):
        """
        初始化检测器

        Args:
            timeout: HTTP 请求超时时间
        """
        self._timeout = timeout or self.CHECK_TIMEOUT
        self._client: Optional[httpx.Client] = None
        self._results: Dict[str, SourceHealthResult] = {}

    def _get_client(self) -> httpx.Client:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def _get_user_github_token(self, user_id: int) -> Optional[str]:
        """
        从用户配置中读取 GitHub Token

        Args:
            user_id: 用户 ID

        Returns:
            GitHub Token 或 None
        """
        try:
            from src.database.connection import get_db_context
            from src.database.models import UserConfig

            with get_db_context() as db:
                config = db.query(UserConfig).filter(
                    UserConfig.user_id == user_id,
                    UserConfig.config_key == "github_token",
                ).first()

                if config and config.config_value:
                    return config.config_value

        except Exception as e:
            logger.warning(f"读取用户 GitHub Token 失败: {e}")

        return None

    def _check_github_graphql(
        self,
        name: str,
        url: str,
        source_type: str,
        token: str,
        prev_failures: int,
    ) -> SourceHealthResult:
        """
        检测 GitHub GraphQL API 连通性

        Args:
            name: 数据源名称
            url: API URL
            source_type: 数据源类型
            token: GitHub Token
            prev_failures: 之前的连续失败次数

        Returns:
            健康检测结果
        """
        try:
            # 使用简单的 GraphQL 查询测试连通性
            query = '{"query": "query { viewer { login } }"}'
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            start_time = time.time()
            response = self._get_client().post(url, content=query, headers=headers)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    error_msg = data["errors"][0].get("message", "GraphQL 错误")
                    return SourceHealthResult(
                        source_name=name,
                        source_type=source_type,
                        url=url,
                        is_healthy=False,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time_ms,
                        last_check_at=datetime.now(),
                        error_message=f"Token 无效: {error_msg}",
                        consecutive_failures=prev_failures + 1,
                    )

                return SourceHealthResult(
                    source_name=name,
                    source_type=source_type,
                    url=url,
                    is_healthy=True,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time_ms,
                    last_check_at=datetime.now(),
                    error_message=None,
                    consecutive_failures=0,
                )

            elif response.status_code == 401:
                return SourceHealthResult(
                    source_name=name,
                    source_type=source_type,
                    url=url,
                    is_healthy=False,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    last_check_at=datetime.now(),
                    error_message="GitHub Token 无效或已过期",
                    consecutive_failures=prev_failures + 1,
                )

            else:
                return SourceHealthResult(
                    source_name=name,
                    source_type=source_type,
                    url=url,
                    is_healthy=False,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time_ms,
                    last_check_at=datetime.now(),
                    error_message=f"HTTP {response.status_code}",
                    consecutive_failures=prev_failures + 1,
                )

        except httpx.TimeoutException:
            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=False,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self._timeout * 1000,
                last_check_at=datetime.now(),
                error_message="请求超时",
                consecutive_failures=prev_failures + 1,
            )

        except Exception as e:
            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=False,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                last_check_at=datetime.now(),
                error_message=str(e)[:100],
                consecutive_failures=prev_failures + 1,
            )

    def _check_public_api(
        self,
        name: str,
        url: str,
        source_type: str,
        prev_failures: int,
    ) -> SourceHealthResult:
        """
        检测公开 API（无需认证）

        针对 Hacker News 等 Firebase API，验证返回数据内容而非仅依赖 HTTP 状态码。

        Args:
            name: 数据源名称
            url: API URL
            source_type: 数据源类型
            prev_failures: 之前的连续失败次数

        Returns:
            健康检测结果
        """
        try:
            # 添加标准请求头，避免被 API 拒绝
            headers = {
                "User-Agent": "Prism-HealthChecker/2.1",
                "Accept": "application/json, text/plain, */*",
            }

            start_time = time.time()
            response = self._get_client().get(url, headers=headers)
            response_time_ms = (time.time() - start_time) * 1000

            # 尝试解析响应内容验证数据有效性
            is_healthy = False
            error_msg = None

            if response.status_code == 200:
                # 检查返回数据是否有效
                try:
                    data = response.json()
                    # Hacker News 返回 ID 数组，V2EX API 返回话题数组
                    if isinstance(data, list) and len(data) > 0:
                        is_healthy = True
                    elif isinstance(data, dict) and len(data) > 0:
                        # 可能是其他 JSON 对象格式
                        is_healthy = True
                    else:
                        error_msg = "返回数据为空或格式异常"
                except Exception:
                    # 非 JSON 响应，检查文本内容
                    if response.text and len(response.text) > 10:
                        is_healthy = True
                    else:
                        error_msg = "响应内容为空"

            elif response.status_code in (401, 403):
                # 公开 API 返回 401/403 可能是临时问题，尝试检查响应内容
                try:
                    data = response.json()
                    if isinstance(data, (list, dict)) and len(data) > 0:
                        # Firebase 有时返回数据但状态码异常，仍视为健康
                        is_healthy = True
                        logger.warning(f"{name} 返回 {response.status_code} 但数据有效，视为健康")
                    else:
                        error_msg = f"HTTP {response.status_code} - 无有效数据"
                except Exception:
                    error_msg = f"HTTP {response.status_code}"

            else:
                error_msg = f"HTTP {response.status_code}"

            # 判定状态
            if is_healthy:
                if response_time_ms > self.RESPONSE_TIME_DEGRADED_MS:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                consecutive_failures = 0
            else:
                status = HealthStatus.UNHEALTHY
                consecutive_failures = prev_failures + 1

            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=is_healthy,
                status=status,
                response_time_ms=response_time_ms,
                last_check_at=datetime.now(),
                error_message=error_msg,
                consecutive_failures=consecutive_failures,
            )

        except httpx.TimeoutException:
            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=False,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self._timeout * 1000,
                last_check_at=datetime.now(),
                error_message="请求超时",
                consecutive_failures=prev_failures + 1,
            )

        except Exception as e:
            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=False,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                last_check_at=datetime.now(),
                error_message=str(e)[:100],
                consecutive_failures=prev_failures + 1,
            )

    def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def check_source(self, source: Dict, user_id: int = None) -> SourceHealthResult:
        """
        检测单个数据源

        Args:
            source: 数据源配置
            user_id: 用户 ID（用于读取用户配置的 token）

        Returns:
            健康检测结果
        """
        name = source["name"]
        url = source["url"]
        source_type = source["type"]
        requires_auth = source.get("requires_auth", False)

        # 获取之前的连续失败次数
        prev_result = self._results.get(name)
        prev_failures = prev_result.consecutive_failures if prev_result else 0

        try:
            client = self._get_client()

            # 构建请求
            headers = {}

            # 公开 API 特殊处理（如 Hacker News Firebase API）
            is_public = source.get("is_public", False)
            if is_public and source_type == "api":
                return self._check_public_api(name, url, source_type, prev_failures)

            if source_type == "api" and "graphql" in url:
                # GraphQL 端点需要认证
                if "github" in url:
                    # 检查用户是否配置了 GitHub Token
                    token = self._get_user_github_token(user_id) if user_id else None
                    
                    if not token:
                        return SourceHealthResult(
                            source_name=name,
                            source_type=source_type,
                            url=url,
                            is_healthy=False,
                            status=HealthStatus.NOT_CONFIGURED,
                            response_time_ms=0,
                            last_check_at=datetime.now(),
                            error_message="需要在配置页填入 GitHub Token 才能使用此数据源",
                            consecutive_failures=0,
                        )
                    
                    # 有 token，执行实际检测
                    return self._check_github_graphql(name, url, source_type, token, prev_failures)

            start_time = time.time()
            response = client.get(url, headers=headers)
            response_time_ms = (time.time() - start_time) * 1000

            is_healthy = response.status_code < 400

            # 判定状态
            if not is_healthy:
                status = HealthStatus.UNHEALTHY
                error_msg = f"HTTP {response.status_code}"
                consecutive_failures = prev_failures + 1
            elif response_time_ms > self.RESPONSE_TIME_UNHEALTHY_MS:
                status = HealthStatus.UNHEALTHY
                error_msg = f"响应超时: {response_time_ms:.0f}ms"
                consecutive_failures = prev_failures + 1
            elif response_time_ms > self.RESPONSE_TIME_DEGRADED_MS:
                status = HealthStatus.DEGRADED
                error_msg = None
                consecutive_failures = 0
            else:
                status = HealthStatus.HEALTHY
                error_msg = None
                consecutive_failures = 0

            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=is_healthy,
                status=status,
                response_time_ms=response_time_ms,
                last_check_at=datetime.now(),
                error_message=error_msg,
                consecutive_failures=consecutive_failures,
            )

        except httpx.TimeoutException:
            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=False,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self._timeout * 1000,
                last_check_at=datetime.now(),
                error_message="请求超时",
                consecutive_failures=prev_failures + 1,
            )

        except Exception as e:
            return SourceHealthResult(
                source_name=name,
                source_type=source_type,
                url=url,
                is_healthy=False,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                last_check_at=datetime.now(),
                error_message=str(e)[:100],
                consecutive_failures=prev_failures + 1,
            )

    def check_all_sources(self, sources: List[Dict] = None, user_id: int = None) -> List[SourceHealthResult]:
        """
        检测所有数据源

        Args:
            sources: 数据源列表（默认使用内置列表）
            user_id: 用户 ID（用于读取用户配置的 token）

        Returns:
            所有数据源健康检测结果
        """
        sources = sources or self.BUILTIN_SOURCES
        results = []

        for source in sources:
            result = self.check_source(source, user_id=user_id)
            self._results[source["name"]] = result
            results.append(result)

            # 记录日志
            status_icon = "✅" if result.status == HealthStatus.HEALTHY else \
                         "⚠️" if result.status == HealthStatus.DEGRADED else \
                         "🔒" if result.status == HealthStatus.NOT_CONFIGURED else "❌"
            logger.info(f"{status_icon} {result.source_name}: {result.status.value} ({result.response_time_ms:.0f}ms)")

        return results

    def get_health_summary(self) -> Dict:
        """
        获取健康状态摘要

        Returns:
            摘要信息
        """
        if not self._results:
            return {
                "total": 0,
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "health_rate": 0,
                "last_check_at": None,
                "sources": [],
            }

        sources = list(self._results.values())
        healthy = sum(1 for s in sources if s.status == HealthStatus.HEALTHY)
        degraded = sum(1 for s in sources if s.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for s in sources if s.status == HealthStatus.UNHEALTHY)
        total = len(sources)

        # 计算健康率（健康 + 降级）/ 总数
        health_rate = (healthy + degraded) / total if total > 0 else 0

        # 最近检测时间
        last_check = max(s.last_check_at for s in sources) if sources else None

        return {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "health_rate": round(health_rate, 2),
            "last_check_at": last_check.isoformat() if last_check else None,
            "sources": [s.to_dict() for s in sources],
        }

    def get_source_health(self, source_name: str) -> Optional[SourceHealthResult]:
        """
        获取单个数据源健康状态

        Args:
            source_name: 数据源名称

        Returns:
            健康检测结果
        """
        return self._results.get(source_name)


# ==========================================
# API 路由
# ==========================================

def create_health_router():
    """创建健康检测 API 路由"""
    from fastapi import APIRouter, Depends
    from src.auth.dependencies import get_current_user_optional
    from src.database.models import User

    router = APIRouter(prefix="/api/sources", tags=["sources"])

    @router.get("/health")
    def get_sources_health(current_user: User = Depends(get_current_user_optional)):
        """
        获取所有数据源健康状态

        Args:
            current_user: 当前登录用户（可选）

        Returns:
            健康状态摘要
        """
        user_id = current_user.id if current_user else None
        with SourceHealthChecker() as checker:
            checker.check_all_sources(user_id=user_id)
            return checker.get_health_summary()

    @router.get("/health/{source_name}")
    def get_source_health(
        source_name: str,
        current_user: User = Depends(get_current_user_optional)
    ):
        """
        获取单个数据源健康状态

        Args:
            source_name: 数据源名称
            current_user: 当前登录用户（可选）

        Returns:
            健康检测结果
        """
        user_id = current_user.id if current_user else None
        with SourceHealthChecker() as checker:
            # 查找数据源
            source = None
            for s in SourceHealthChecker.BUILTIN_SOURCES:
                if s["name"] == source_name:
                    source = s
                    break

            if not source:
                return {"error": f"数据源不存在: {source_name}"}

            result = checker.check_source(source, user_id=user_id)
            return result.to_dict()

    @router.post("/health/check")
    def trigger_health_check(current_user: User = Depends(get_current_user_optional)):
        """
        手动触发健康检测

        Args:
            current_user: 当前登录用户（可选）

        Returns:
            健康状态摘要
        """
        user_id = current_user.id if current_user else None
        with SourceHealthChecker() as checker:
            checker.check_all_sources(user_id=user_id)
            return checker.get_health_summary()

    return router


# ==========================================
# 便捷函数
# ==========================================

def check_sources_health() -> Dict:
    """
    检测所有数据源健康状态（便捷函数）

    Returns:
        健康状态摘要
    """
    with SourceHealthChecker() as checker:
        checker.check_all_sources()
        return checker.get_health_summary()


def check_single_source(source_name: str, url: str, source_type: str = "api") -> Dict:
    """
    检测单个数据源（便捷函数）

    Args:
        source_name: 数据源名称
        url: URL
        source_type: 类型

    Returns:
        健康检测结果
    """
    with SourceHealthChecker() as checker:
        result = checker.check_source({
            "name": source_name,
            "url": url,
            "type": source_type,
        })
        return result.to_dict()


# ==========================================
# CLI 入口
# ==========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据源健康检测")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    with SourceHealthChecker() as checker:
        results = checker.check_all_sources()
        summary = checker.get_health_summary()

        if args.json:
            import json
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print(f"\n数据源健康状态: {summary['healthy']}/{summary['total']} 健康")
            print("=" * 50)

            for result in results:
                icon = "✅" if result.status == HealthStatus.HEALTHY else \
                       "⚠️" if result.status == HealthStatus.DEGRADED else "❌"
                print(f"{icon} {result.source_name}: {result.status.value} ({result.response_time_ms:.0f}ms)")
                if result.error_message:
                    print(f"   错误: {result.error_message}")