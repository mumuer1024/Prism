"""
Commercial Agent - GitHub Trending Sensor (GraphQL API Version)

Uses GitHub GraphQL API to find high-potential repositories.
Focuses on "Breakout" repos: created recently with high star velocity.

Dependencies: httpx (or requests)
Usage: python github_trending.py [language]
"""

import os
import sys
import datetime
from dataclasses import dataclass, field
from typing import Optional

# Use httpx if available, fall back to requests
try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    try:
        import requests
        HTTP_CLIENT = "requests"
    except ImportError:
        HTTP_CLIENT = None

GITHUB_API_URL = "https://api.github.com/graphql"

@dataclass
class GitHubTrend:
    """A single trending repository."""
    name: str                   # e.g., "owner/repo"
    url: str
    description: str
    language: Optional[str]
    stars: int
    forks: int
    created_at: str
    pushed_at: str
    readme_text: Optional[str] = None  # Fetched via GraphQL
    hype_score: int = field(init=False)

    def __post_init__(self):
        # Calculate hype: stars relative to age would be cool,
        # but for now simple log scale of stars for "recently created" items
        import math
        # If it's new (search query ensures this), raw stars is a good proxy for hype
        self.hype_score = min(100, int(math.log10(max(self.stars, 1)) * 25))


def get_user_github_token(user_id: int) -> Optional[str]:
    """
    从用户配置中读取 GitHub Token

    Args:
        user_id: 用户 ID

    Returns:
        GitHub Token 字符串，未配置则返回 None
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
        print(f"读取用户 GitHub Token 失败: {e}")

    return None


def fetch_trending(language: Optional[str] = None, user_id: Optional[int] = None, token: Optional[str] = None) -> list[GitHubTrend]:
    """
    Fetch trending repositories using GitHub GraphQL API.
    Strategy: Search for repos created in the last 7 days, sorted by stars.

    Args:
        language: 可选的语言筛选
        user_id: 用户 ID（从用户配置读取 token）
        token: 直接传入的 token（优先级最高）

    Returns:
        GitHubTrend 列表

    Raises:
        ValueError: 未提供 token 且用户未配置 GitHub Token
    """
    # Token 优先级：直接传入 > 环境变量 USER_GITHUB_TOKEN > 全局 .env > 用户配置
    if not token:
        token = os.getenv("USER_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    
    if not token and user_id:
        token = get_user_github_token(user_id)

    if not token:
        raise ValueError("GitHub Token 未配置。请在配置页填入 GitHub Token 后重试。")

    if HTTP_CLIENT is None:
        print("ERROR: No HTTP client available. Install httpx or requests.")
        return []

    # Calculate date 7 days ago
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Build Search Query
    # Query: "created:>YYYY-MM-DD sort:stars"
    search_query = f"created:>{seven_days_ago} sort:stars"
    if language:
        search_query += f" language:{language}"

    graphql_query = """
    query($search_query: String!) {
      search(query: $search_query, type: REPOSITORY, first: 10) {
        edges {
          node {
            ... on Repository {
              nameWithOwner
              url
              description
              stargazerCount
              forkCount
              createdAt
              pushedAt
              primaryLanguage {
                name
              }
              object(expression: "HEAD:README.md") {
                ... on Blob {
                  text
                }
              }
            }
          }
        }
      }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Commercial-Agent-Sensor"
    }

    payload = {
        "query": graphql_query,
        "variables": {"search_query": search_query}
    }
    
    try:
        print(f"  → Sending GraphQL query to GitHub ({search_query})...")
        if HTTP_CLIENT == "httpx":
            response = httpx.post(GITHUB_API_URL, json=payload, headers=headers, timeout=30.0)
        else:
            response = requests.post(GITHUB_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"ERROR: API returned {response.status_code}")
            print(response.text)
            return []
            
        data = response.json()
        if "errors" in data:
            print(f"ERROR: GraphQL errors: {data['errors']}")
            return []

        return _parse_graphql_response(data)

    except Exception as e:
        print(f"ERROR: Request failed: {e}")
        return []

def _parse_graphql_response(data: dict) -> list[GitHubTrend]:
    trends = []
    edges = data.get("data", {}).get("search", {}).get("edges", [])
    
    for edge in edges:
        node = edge.get("node")
        if not node:
            continue
            
        # Extract README
        readme_obj = node.get("object")
        readme_text = readme_obj.get("text", "") if readme_obj else ""
            
        trends.append(GitHubTrend(
            name=node["nameWithOwner"],
            url=node["url"],
            description=node["description"] or "(No description)",
            language=node["primaryLanguage"]["name"] if node["primaryLanguage"] else None,
            stars=node["stargazerCount"],
            forks=node["forkCount"],
            created_at=node["createdAt"],
            pushed_at=node["pushedAt"],
            readme_text=readme_text[:5000]  # Truncate to save memory/tokens
        ))
        
    return trends

def print_trends(trends: list[GitHubTrend]) -> None:
    print(f"\n{'='*60}")
    print(f" 🚀 Breakout Repos (Last 7 Days) - Top {len(trends)}")
    print(f"{'='*60}\n")

    for i, t in enumerate(trends, 1):
        print(f"{i}. [{t.hype_score:3d}] {t.name}")
        print(f"   ⭐ {t.stars} | 🍴 {t.forks} | Created: {t.created_at[:10]}")
        if t.language:
            print(f"   📝 {t.language}")
        print(f"   {t.description[:100]}...")
        print(f"   🔗 {t.url}")
        print()

def trigger_ghostwriter(trend: GitHubTrend):
    """Invoke the Ghostwriter skill to draft an article."""
    import subprocess
    import tempfile
    
    print(f"  → ✍️ Triggering Curator (Analyst) for {trend.name}...")
    
    # Create temp file for readme context
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.txt') as f:
        f.write(trend.readme_text or "(No README)")
        readme_path = f.name
        
    try:
        # Call the Curator script
        script_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Generators", "Curator", "curator.py")
        script_path = os.path.abspath(script_path)
        
        # Clean name for filename
        safe_name = trend.name.replace('/', '_')
        output_name = f"{safe_name}_briefing.md"
        
        cmd = [
            sys.executable, script_path,
            "--repo-name", trend.name,
            "--readme", readme_path,
            "--output", output_name
        ]
        
        # Run it
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        print(f"  ❌ Curator failed: {e}")
    finally:
        os.unlink(readme_path)

if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else None
    trends = fetch_trending(lang)
    if trends:
        print_trends(trends)
        
        # MVP: Auto-trigger for the Top 1 item
        top_trend = trends[0]
        print(f"\n[Commercial Agent] 🧠 Automatically analyzing top opportunity: {top_trend.name}")
        trigger_ghostwriter(top_trend)
        
    else:
        print("No trends found.")
