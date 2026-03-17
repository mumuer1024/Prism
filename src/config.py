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