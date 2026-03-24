# -*- coding: utf-8 -*-
"""
数据库连接模块

提供 SQLAlchemy 数据库连接和会话管理
"""

import os
import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from src.config import settings

logger = logging.getLogger(__name__)

# 创建 Base 类
Base = declarative_base()

# 数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'prism.db')}"
)

# 创建引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite 配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL / MySQL 配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG,
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入：获取数据库会话
    
    使用方式：
        @router.post("/example")
        def example(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    上下文管理器：获取数据库会话
    
    使用方式：
        with get_db_context() as db:
            db.query(User).all()
    
    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def init_database():
    """
    初始化数据库

    创建所有表结构
    """
    # 确保数据目录存在
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 导入所有模型以确保它们被注册
    from src.database.models import (
        User,
        AnonymousUser,
        VerificationCode,
        RefreshToken,
        RedemptionCode,
        TopupRecord,
        InviteRecord,
        Admin,
        Report,
        SchemaVersion,
        # V2.0 第二阶段新增模型
        PresetSource,
        CustomSource,
        PresetPrompt,
        CustomPrompt,
        UserSourceSubscription,
        MarketplaceCategory,
        MarketplaceLike,
        MarketplaceFavorite,
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成")

    # 检查并运行迁移脚本
    _run_migrations()


def _run_migrations():
    """
    运行数据库迁移脚本

    检查 schema_version 表，执行未应用的迁移
    """
    db = SessionLocal()
    try:
        # 检查是否需要初始化版本表
        from src.database.models import SchemaVersion

        # 获取当前版本
        latest_version = db.query(SchemaVersion).order_by(
            SchemaVersion.version.desc()
        ).first()

        current_version = latest_version.version if latest_version else 0

        if current_version < 1:
            # 版本 1: 初始表结构（已在 create_all 中创建）
            version_record = SchemaVersion(
                version=1,
                description="初始表结构：用户、验证码、Token、兑换码等"
            )
            db.add(version_record)
            db.commit()
            logger.info("数据库迁移: 版本 1 已应用")

        if current_version < 2:
            # 版本 2: V2.0 第二阶段 - 自定义信息源、Prompt、预设广场
            _apply_migration_v2(db)
            version_record = SchemaVersion(
                version=2,
                description="V2.0 第二阶段：自定义信息源、自定义 Prompt、预设广场"
            )
            db.add(version_record)
            db.commit()
            logger.info("数据库迁移: 版本 2 已应用")

        # 未来迁移示例：
        # if current_version < 3:
        #     _apply_migration_v3()

    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        db.rollback()
    finally:
        db.close()


def _apply_migration_v2(db):
    """
    版本 2 迁移：初始化预设数据

    - 创建广场分类
    - 创建预设信息源
    - 创建预设 Prompt 模板
    """
    from src.database.models import (
        MarketplaceCategory,
        PresetSource,
        PresetPrompt,
    )

    # 1. 创建广场分类
    categories = [
        # 信息源分类
        {"name": "技术趋势", "type": "source", "icon": "code", "sort_order": 1},
        {"name": "财经资讯", "type": "source", "icon": "trending-up", "sort_order": 2},
        {"name": "社交热点", "type": "source", "icon": "users", "sort_order": 3},
        {"name": "学术研究", "type": "source", "icon": "book-open", "sort_order": 4},
        {"name": "产品发现", "type": "source", "icon": "box", "sort_order": 5},
        {"name": "商业机会", "type": "source", "icon": "dollar-sign", "sort_order": 6},
        # Prompt 分类
        {"name": "报告生成", "type": "prompt", "icon": "file-text", "sort_order": 1},
        {"name": "内容摘要", "type": "prompt", "icon": "align-left", "sort_order": 2},
        {"name": "深度分析", "type": "prompt", "icon": "search", "sort_order": 3},
        {"name": "翻译润色", "type": "prompt", "icon": "globe", "sort_order": 4},
    ]

    for cat_data in categories:
        existing = db.query(MarketplaceCategory).filter(
            MarketplaceCategory.name == cat_data["name"],
            MarketplaceCategory.type == cat_data["type"]
        ).first()
        if not existing:
            category = MarketplaceCategory(**cat_data)
            db.add(category)

    db.flush()

    # 2. 创建预设信息源
    preset_sources = [
        # 免费信息源
        {
            "key": "hacker_news",
            "name": "Hacker News",
            "category": "tech",
            "description": "全球顶级技术社区，追踪最新技术趋势和开发者讨论",
            "icon": "hn",
            "source_type": "api",
            "config": '{"url": "https://hacker-news.firebaseio.com/v0/topstories.json", "item_url": "https://hacker-news.firebaseio.com/v0/item/{}.json"}',
            "is_free": True,
            "requires_api_key": False,
            "sort_order": 1,
        },
        {
            "key": "github_trending",
            "name": "GitHub Trending",
            "category": "tech",
            "description": "GitHub 热门开源项目，发现最新技术趋势",
            "icon": "github",
            "source_type": "api",
            "config": '{"url": "https://api.github.com/search/repositories", "params": {"q": "stars:>100", "sort": "stars", "order": "desc"}}',
            "is_free": True,
            "requires_api_key": True,
            "api_key_env": "GITHUB_TOKEN",
            "sort_order": 2,
        },
        {
            "key": "product_hunt",
            "name": "Product Hunt",
            "category": "product",
            "description": "新产品发布平台，发现最新产品和创业项目",
            "icon": "ph",
            "source_type": "api",
            "config": '{"url": "https://api.producthunt.com/v2/api/graphql"}',
            "is_free": True,
            "requires_api_key": True,
            "api_key_env": "PRODUCTHUNT_TOKEN",
            "sort_order": 3,
        },
        {
            "key": "36kr",
            "name": "36氪",
            "category": "finance",
            "description": "中文科技财经媒体，追踪国内科技动态",
            "icon": "36kr",
            "source_type": "scraper",
            "config": '{"url": "https://36kr.com/newsflashes"}',
            "is_free": True,
            "requires_api_key": False,
            "sort_order": 4,
        },
        # 付费信息源
        {
            "key": "arxiv",
            "name": "ArXiv AI/ML",
            "category": "research",
            "description": "AI/ML 学术论文预印本，追踪学术前沿",
            "icon": "arxiv",
            "source_type": "api",
            "config": '{"url": "http://export.arxiv.org/api/query", "params": {"search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL", "max_results": 20}}',
            "is_free": False,
            "requires_api_key": False,
            "sort_order": 10,
        },
        {
            "key": "v2ex",
            "name": "V2EX",
            "category": "social",
            "description": "中文技术社区，开发者交流平台",
            "icon": "v2ex",
            "source_type": "scraper",
            "config": '{"url": "https://www.v2ex.com/api/topics/hot.json"}',
            "is_free": False,
            "requires_api_key": False,
            "sort_order": 11,
        },
        {
            "key": "wallstreet",
            "name": "华尔街见闻",
            "category": "finance",
            "description": "专业财经资讯，全球市场动态",
            "icon": "ws",
            "source_type": "scraper",
            "config": '{"url": "https://wallstreetcn.com/news/global"}',
            "is_free": False,
            "requires_api_key": False,
            "sort_order": 12,
        },
        {
            "key": "x_grok",
            "name": "X/Twitter (Grok)",
            "category": "social",
            "description": "通过 Grok API 获取 X 平台实时讨论",
            "icon": "twitter",
            "source_type": "api",
            "config": '{"provider": "xai", "model": "grok-beta"}',
            "is_free": False,
            "requires_api_key": True,
            "api_key_env": "XAI_API_KEY",
            "sort_order": 13,
        },
        {
            "key": "hn_blogs",
            "name": "HN Top Blogs",
            "category": "tech",
            "description": "Hacker News 热门博客文章深度分析",
            "icon": "blog",
            "source_type": "scraper",
            "config": '{"source": "hn_blogs"}',
            "is_free": False,
            "requires_api_key": False,
            "sort_order": 14,
        },
        {
            "key": "chrome_store",
            "name": "Chrome 扩展雷达",
            "category": "business",
            "description": "Chrome Web Store 商业机会发现",
            "icon": "chrome",
            "source_type": "scraper",
            "config": '{"url": "https://chrome.google.com/webstore/sitemap"}',
            "is_free": False,
            "requires_api_key": False,
            "sort_order": 15,
        },
        {
            "key": "xhs",
            "name": "小红书雷达",
            "category": "business",
            "description": "小红书消费趋势和商业机会",
            "icon": "xhs",
            "source_type": "scraper",
            "config": '{"source": "xhs_radar"}',
            "is_free": False,
            "requires_api_key": False,
            "sort_order": 16,
        },
    ]

    for source_data in preset_sources:
        existing = db.query(PresetSource).filter(
            PresetSource.key == source_data["key"]
        ).first()
        if not existing:
            source = PresetSource(**source_data)
            db.add(source)

    db.flush()

    # 3. 创建预设 Prompt 模板
    preset_prompts = [
        # 免费模板
        {
            "key": "daily_brief",
            "name": "每日简报",
            "category": "report",
            "description": "生成结构化的每日情报简报",
            "template_content": """# 🌐 每日情报简报
**日期:** {{date}}

## 📊 今日概览
{{summary}}

## 🔥 热点追踪
{{#each hot_items}}
- **{{title}}**: {{brief}}
{{/each}}

## 💡 行动建议
{{recommendations}}""",
            "variables": '[{"name": "date", "type": "string", "required": true}, {"name": "summary", "type": "string", "required": true}, {"name": "hot_items", "type": "array", "required": true}, {"name": "recommendations", "type": "string", "required": false}]',
            "is_free": True,
            "sort_order": 1,
        },
        {
            "key": "tech_summary",
            "name": "技术摘要",
            "category": "summary",
            "description": "技术文章智能摘要",
            "template_content": """请对以下技术内容进行摘要：

{{content}}

要求：
1. 提取核心观点（3-5 条）
2. 总结技术要点
3. 给出学习建议

输出格式：
## 核心观点
- ...

## 技术要点
- ...

## 学习建议
...""",
            "variables": '[{"name": "content", "type": "string", "required": true}]',
            "is_free": True,
            "sort_order": 2,
        },
        # 付费模板
        {
            "key": "deep_analysis",
            "name": "深度分析报告",
            "category": "analysis",
            "description": "对特定主题进行深度分析，生成专业报告",
            "template_content": """你是一位专业的{{domain}}分析师。请对以下内容进行深度分析：

## 分析对象
{{subject}}

## 背景信息
{{background}}

## 分析要求
1. 行业现状分析
2. 竞争格局评估
3. 发展趋势预测
4. 风险与机遇分析
5. 行动建议

请以专业报告格式输出，包含数据支撑和逻辑推理。""",
            "variables": '[{"name": "domain", "type": "string", "required": true, "default": "技术"}, {"name": "subject", "type": "string", "required": true}, {"name": "background", "type": "string", "required": false}]',
            "is_free": False,
            "sort_order": 10,
        },
        {
            "key": "translate_polish",
            "name": "翻译润色",
            "category": "translate",
            "description": "高质量翻译并润色文本",
            "template_content": """请将以下{{source_lang}}文本翻译为{{target_lang}}，并进行润色：

## 原文
{{text}}

## 要求
1. 准确传达原意
2. 符合目标语言表达习惯
3. 保持专业性和可读性
4. 如有术语，请保留原文并标注

## 输出
### 翻译
[翻译内容]

### 润色说明
[如有调整，请说明]""",
            "variables": '[{"name": "source_lang", "type": "string", "required": true, "default": "英文"}, {"name": "target_lang", "type": "string", "required": true, "default": "中文"}, {"name": "text", "type": "string", "required": true}]',
            "is_free": False,
            "sort_order": 11,
        },
        {
            "key": "competitor_analysis",
            "name": "竞品分析",
            "category": "analysis",
            "description": "分析竞争对手产品，生成竞品报告",
            "template_content": """请对以下竞品进行分析：

## 目标产品
{{product_name}}
{{product_url}}

## 分析维度
1. 产品定位与目标用户
2. 核心功能与特色
3. 商业模式分析
4. 优势与不足
5. 市场表现评估
6. 对我方产品的启示

## 已知信息
{{known_info}}

请输出详细的竞品分析报告。""",
            "variables": '[{"name": "product_name", "type": "string", "required": true}, {"name": "product_url", "type": "string", "required": false}, {"name": "known_info", "type": "string", "required": false}]',
            "is_free": False,
            "sort_order": 12,
        },
    ]

    for prompt_data in preset_prompts:
        existing = db.query(PresetPrompt).filter(
            PresetPrompt.key == prompt_data["key"]
        ).first()
        if not existing:
            prompt = PresetPrompt(**prompt_data)
            db.add(prompt)

    db.commit()
    logger.info("V2.0 预设数据初始化完成")


def close_database():
    """
    关闭数据库连接
    
    在应用关闭时调用
    """
    engine.dispose()
    logger.info("数据库连接已关闭")


# SQLite 优化：启用外键约束
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()