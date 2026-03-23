"""
Intel Briefing - 统一配置模块（更新版）
支持 OpenAI 兼容 / Gemini 原生 / Claude 原生 三种 API 格式
"""
import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# --- Logging ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", log_file: str = None):
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=handlers,
        force=True,
    )


# --- 数据源 API Keys ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PRODUCTHUNT_TOKEN = os.getenv("PRODUCTHUNT_TOKEN")

# --- XAI / X/Twitter 搜索端点（仅用于 Grok 访问 X 实时数据）---
# 注意：XAI_API_KEY 仅用于 x_grok_sensor.py（X/Twitter 搜索）
# 因为只有 Grok 能访问 X 实时数据，必须使用 xAI 官方 API
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1/chat/completions")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-beta")
XAI_API_FORMAT = os.getenv("XAI_API_FORMAT", "openai")   # openai | gemini | claude

# --- 通用推理模型端点（营收分析等任务）---
# 支持任意 OpenAI 兼容端点（NewAPI / OpenRouter / 官方等）
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_FORMAT = os.getenv("LLM_API_FORMAT", "openai")   # openai | gemini | claude

# --- 翻译模型端点（原 Gemini，现支持任意格式）---
TRANSLATOR_API_KEY = os.getenv("TRANSLATOR_API_KEY") or os.getenv("GEMINI_API_KEY")
TRANSLATOR_BASE_URL = os.getenv(
    "TRANSLATOR_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/models"
)
TRANSLATOR_MODEL = os.getenv("TRANSLATOR_MODEL", "gemini-2.5-flash-lite")
TRANSLATOR_API_FORMAT = os.getenv("TRANSLATOR_API_FORMAT", "gemini")  # openai | gemini | claude

# --- 向后兼容（旧代码直接 import 这些变量的地方不会报错）---
GEMINI_API_KEY = TRANSLATOR_API_KEY
GEMINI_API_URL = TRANSLATOR_BASE_URL
GEMINI_MODEL = TRANSLATOR_MODEL

# --- API Endpoints (非 AI) ---
GITHUB_API_URL = "https://api.github.com/graphql"
JINA_READER_URL = "https://r.jina.ai/"

# --- Timeouts (seconds) ---
DEFAULT_TIMEOUT = 15
GEMINI_TIMEOUT = 60
JINA_TIMEOUT = 30
GROK_TIMEOUT = 60

# --- Content Limits ---
CONTENT_TRUNCATE_LIMIT = 3000
JINA_MAX_CHARS = 15000
PH_HYDRATION_TRUNCATE = 5000
GEMINI_MAX_OUTPUT_TOKENS = 1024
GEMINI_SUMMARY_MAX_TOKENS = 256
GEMINI_DETAIL_MAX_TOKENS = 1024

# --- Rate Limiting ---
GEMINI_RATE_LIMIT_DELAY = 1.5
GEMINI_MAX_RETRIES = 3

# --- Fetch Limits ---
MAX_BLOGS_TO_FETCH = 20
MAX_ARTICLES_PER_BLOG = 2
RSS_FETCH_TIMEOUT = 10

# --- 数据源开关配置 ---
def _parse_bool(val: str | None, default: bool = True) -> bool:
    """解析布尔值，支持 true/yes/1/false/no/0 等格式"""
    if val is None:
        return default
    return val.lower() in ('true', 'yes', '1', 'on', 'enabled')

# 各数据源启用开关（默认全部启用）
SOURCE_ENABLED_HACKERNEWS = _parse_bool(os.getenv("SOURCE_ENABLED_HACKERNEWS"), True)
SOURCE_ENABLED_GITHUB_TRENDING = _parse_bool(os.getenv("SOURCE_ENABLED_GITHUB_TRENDING"), True)
SOURCE_ENABLED_ARXIV = _parse_bool(os.getenv("SOURCE_ENABLED_ARXIV"), True)
SOURCE_ENABLED_PRODUCTHUNT = _parse_bool(os.getenv("SOURCE_ENABLED_PRODUCTHUNT"), True)
SOURCE_ENABLED_V2EX = _parse_bool(os.getenv("SOURCE_ENABLED_V2EX"), True)
SOURCE_ENABLED_36KR = _parse_bool(os.getenv("SOURCE_ENABLED_36KR"), True)
SOURCE_ENABLED_WALLSTREET = _parse_bool(os.getenv("SOURCE_ENABLED_WALLSTREET"), True)
SOURCE_ENABLED_X_GROK = _parse_bool(os.getenv("SOURCE_ENABLED_X_GROK"), True)
SOURCE_ENABLED_HN_BLOGS = _parse_bool(os.getenv("SOURCE_ENABLED_HN_BLOGS"), True)
SOURCE_ENABLED_CHROME = _parse_bool(os.getenv("SOURCE_ENABLED_CHROME"), True)
SOURCE_ENABLED_XHS = _parse_bool(os.getenv("SOURCE_ENABLED_XHS"), True)


# ============================================================
# V2.0 用户系统配置
# ============================================================

# --- 基础配置 ---
DEBUG = _parse_bool(os.getenv("DEBUG"), False)
APP_NAME = os.getenv("APP_NAME", "Prism")
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")

# --- JWT 配置 ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "prism-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))  # 2 小时
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 7 天

# --- 验证码配置 ---
VERIFY_CODE_LENGTH = int(os.getenv("VERIFY_CODE_LENGTH", "6"))
VERIFY_CODE_EXPIRE_MINUTES = int(os.getenv("VERIFY_CODE_EXPIRE_MINUTES", "5"))
VERIFY_CODE_RESEND_SECONDS = int(os.getenv("VERIFY_CODE_RESEND_SECONDS", "60"))

# --- 邮件配置（自建 SMTP）---
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")

# --- 腾讯云邮件配置 ---
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")

# --- GitHub OAuth ---
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback")

# --- 微信 OAuth ---
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
WECHAT_REDIRECT_URI = os.getenv("WECHAT_REDIRECT_URI", "http://localhost:8000/api/auth/wechat/callback")

# --- 免费用户配置 ---
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "3"))
FREE_SOURCES = os.getenv("FREE_SOURCES", "hacker_news,product_hunt,github_trending,36kr").split(",")
FREE_TOOLS = os.getenv("FREE_TOOLS", "bounty_hunter,alpha_radar,revenue_architect,narrator").split(",")

# --- 缓存配置 ---
FREE_CACHE_HOURS = int(os.getenv("FREE_CACHE_HOURS", "6"))  # 免费用户缓存时间
PREMIUM_CACHE_HOURS = int(os.getenv("PREMIUM_CACHE_HOURS", "1"))  # 付费用户缓存时间

# --- 邀请返利配置 ---
INVITE_BONUS_COUNT = int(os.getenv("INVITE_BONUS_COUNT", "3"))  # 邀请返利次数
INVITEE_BONUS_COUNT = int(os.getenv("INVITEE_BONUS_COUNT", "3"))  # 被邀请人奖励次数

# --- 兑换码配置 ---
REDEMPTION_CODE_PREFIX = os.getenv("REDEMPTION_CODE_PREFIX", "PRISM-")
REDEMPTION_CODE_LENGTH = int(os.getenv("REDEMPTION_CODE_LENGTH", "8"))

# --- 邀请码配置 ---
INVITE_CODE_PREFIX = os.getenv("INVITE_CODE_PREFIX", "PRISM-")
INVITE_CODE_LENGTH = int(os.getenv("INVITE_CODE_LENGTH", "8"))

# --- 数据库配置 ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/prism.db")

# --- 功能开关 ---
FEATURE_USER_SYSTEM = _parse_bool(os.getenv("FEATURE_USER_SYSTEM"), True)
FEATURE_OAUTH_GITHUB = _parse_bool(os.getenv("FEATURE_OAUTH_GITHUB"), True)
FEATURE_OAUTH_WECHAT = _parse_bool(os.getenv("FEATURE_OAUTH_WECHAT"), False)
FEATURE_INVITE_SYSTEM = _parse_bool(os.getenv("FEATURE_INVITE_SYSTEM"), True)
FEATURE_FREE_TIER = _parse_bool(os.getenv("FEATURE_FREE_TIER"), True)
FEATURE_REDEMPTION_CODE = _parse_bool(os.getenv("FEATURE_REDEMPTION_CODE"), True)


# ============================================================
# Pydantic Settings 类（推荐使用）
# ============================================================

try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
    from typing import List, Union

    class Settings(BaseSettings):
        """应用配置类"""
        
        # 基础配置
        APP_NAME: str = "Prism"
        APP_VERSION: str = "2.0.0"
        DEBUG: bool = False
        
        # JWT 配置
        JWT_SECRET_KEY: str = "prism-secret-key-change-in-production"
        JWT_ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7
        
        # 验证码配置
        VERIFY_CODE_LENGTH: int = 6
        VERIFY_CODE_EXPIRE_MINUTES: int = 5
        VERIFY_CODE_RESEND_SECONDS: int = 60
        
        # 邮件配置（自建 SMTP）
        SMTP_HOST: str = ""
        SMTP_PORT: int = 587
        SMTP_USER: str = ""
        SMTP_PASSWORD: str = ""
        EMAIL_FROM: str = ""
        
        # 腾讯云邮件配置
        TENCENT_SECRET_ID: str = ""
        TENCENT_SECRET_KEY: str = ""
        
        # GitHub OAuth
        GITHUB_CLIENT_ID: str = ""
        GITHUB_CLIENT_SECRET: str = ""
        GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"
        
        # 微信 OAuth
        WECHAT_APP_ID: str = ""
        WECHAT_APP_SECRET: str = ""
        WECHAT_REDIRECT_URI: str = "http://localhost:8000/api/auth/wechat/callback"
        
        # 免费用户配置
        FREE_DAILY_LIMIT: int = 3
        FREE_SOURCES: Union[str, List[str]] = "hacker_news,product_hunt,github_trending,36kr"
        FREE_TOOLS: Union[str, List[str]] = "bounty_hunter,alpha_radar,revenue_architect,narrator"

        # 缓存配置
        FREE_CACHE_HOURS: int = 6
        PREMIUM_CACHE_HOURS: int = 1
        
        # 邀请返利配置
        INVITE_BONUS_COUNT: int = 3
        INVITEE_BONUS_COUNT: int = 3
        
        # 兑换码配置
        REDEMPTION_CODE_PREFIX: str = "PRISM-"
        REDEMPTION_CODE_LENGTH: int = 8
        
        # 邀请码配置
        INVITE_CODE_PREFIX: str = "PRISM-"
        INVITE_CODE_LENGTH: int = 8
        
        # 数据库配置
        DATABASE_URL: str = "sqlite:///./data/prism.db"
        
        # 功能开关
        FEATURE_USER_SYSTEM: bool = True
        FEATURE_OAUTH_GITHUB: bool = True
        FEATURE_OAUTH_WECHAT: bool = False
        FEATURE_INVITE_SYSTEM: bool = True
        FEATURE_FREE_TIER: bool = True
        FEATURE_REDEMPTION_CODE: bool = True
        
        @field_validator('FREE_SOURCES', 'FREE_TOOLS', mode='before')
        @classmethod
        def parse_list_field(cls, v):
            """解析列表字段，支持逗号分隔字符串或列表"""
            if isinstance(v, str):
                return [item.strip() for item in v.split(',') if item.strip()]
            if isinstance(v, list):
                return v
            return []
        
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": True,
            "extra": "ignore",  # 忽略 .env 中未定义的字段
        }

    # 创建全局配置实例
    settings = Settings()

except ImportError:
    # 如果 pydantic-settings 未安装，使用简单的配置对象
    class Settings:
        """简单配置类（无验证）"""
        pass
    
    settings = Settings()
    
    # 将所有配置变量复制到 settings 对象
    for name, value in list(globals().items()):
        if name.isupper() and not name.startswith('_'):
            setattr(settings, name, value)