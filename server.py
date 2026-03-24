import os
import sys
import json
import asyncio
import subprocess
import zipfile
import io
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import dotenv_values, set_key

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Windows 需要设置 ProactorEventLoop 以支持 subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(
    title="Prism API",
    description="情报聚合系统 API",
    version="2.0.0",
)

# ── CORS 中间件 ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.resolve()
ENV_FILE = BASE_DIR / ".env"
REPORTS_DIR = BASE_DIR / "reports"

# ── Health Check ──────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """健康检查端点（Docker 健康检查使用）"""
    return {"status": "ok"}


# ── Startup & Shutdown Events ──────────────────────────────

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    try:
        # 初始化数据库
        sys.path.insert(0, str(BASE_DIR))
        from src.database.connection import init_database
        init_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    try:
        from src.database.connection import close_database
        close_database()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"数据库关闭失败: {e}")


# ── Register Auth Router ────────────────────────────────────

try:
    from src.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
    logger.info("认证路由注册成功")
except ImportError as e:
    logger.warning(f"认证路由注册失败: {e}")


# ── Register User Router ────────────────────────────────────

try:
    from src.user.router import router as user_router
    app.include_router(user_router, prefix="/api/user", tags=["用户管理"])
    logger.info("用户路由注册成功")
except ImportError as e:
    logger.warning(f"用户路由注册失败: {e}")


# ── Register Usage Router ────────────────────────────────────

try:
    from src.usage.router import router as usage_router
    app.include_router(usage_router, prefix="/api", tags=["使用次数"])
    logger.info("使用次数路由注册成功")
except ImportError as e:
    logger.warning(f"使用次数路由注册失败: {e}")


# ── Register User Config Router ───────────────────────────────

try:
    from src.config_router import router as user_config_router
    app.include_router(user_config_router, prefix="/api/user-config", tags=["用户配置"])
    logger.info("用户配置路由注册成功")
except ImportError as e:
    logger.warning(f"用户配置路由注册失败: {e}")


SCRIPTS = {
    "mission": "run_mission.py",
    "bounty": "run_bounty_hunter.py",
    "alpha": "run_alpha_radar.py",
    "revenue": "run_revenue_architect.py",
}

running_processes = {}


# ── Config ──────────────────────────────────────────────

class EnvUpdate(BaseModel):
    data: dict

@app.get("/api/config")
def get_config():
    if not ENV_FILE.exists():
        return {}
    return dict(dotenv_values(ENV_FILE))

@app.post("/api/config")
def save_config(body: EnvUpdate):
    ENV_FILE.touch()
    for key, value in body.data.items():
        set_key(str(ENV_FILE), key, value)
    return {"ok": True}


# ── Models ───────────────────────────────────────────────

class ModelListRequest(BaseModel):
    base_url: str
    api_key: str
    api_format: str = "openai"

@app.get("/api/models")
async def get_models(base_url: str, api_key: str, api_format: str = "openai"):
    """获取可用模型列表"""
    import sys
    sys.path.insert(0, str(BASE_DIR))
    try:
        from llm_client import list_models
        # 处理 base_url：移除末尾的 /v1/chat/completions 等路径
        processed_url = base_url.rstrip('/')
        if '/v1/chat/completions' in processed_url:
            processed_url = processed_url.replace('/v1/chat/completions', '/v1')
        models = list_models(processed_url, api_key, api_format)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Connection Test ─────────────────────────────────────

class ConnectionTest(BaseModel):
    base_url: str
    api_key: str
    api_format: str = "openai"

@app.post("/api/test-connection")
async def test_connection(body: ConnectionTest):
    """测试 API 连接是否通畅"""
    import time
    start = time.time()

    try:
        # 处理 base_url：移除末尾的 /v1/chat/completions 等路径，保留到 /v1
        base_url = body.base_url.rstrip('/')
        if '/v1/chat/completions' in base_url:
            base_url = base_url.replace('/v1/chat/completions', '/v1')
        elif '/v1/' in base_url and not base_url.endswith('/v1'):
            # 如果 URL 包含 /v1/ 子路径（如 /v1/models），只保留到 /v1
            base_url = base_url[:base_url.index('/v1/') + 3]
        elif not base_url.endswith('/v1'):
            # 如果不以 /v1 结尾，尝试添加 /v1
            base_url = base_url + '/v1'

        if body.api_format == "openai":
            headers = {"Authorization": f"Bearer {body.api_key}"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{base_url}/models",
                    headers=headers,
                    timeout=10.0
                )
                if resp.status_code == 200:
                    latency = int((time.time() - start) * 1000)
                    return {"ok": True, "latency": latency}
                else:
                    return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        else:
            return {"ok": False, "error": f"暂不支持 {body.api_format} 格式的连通性测试"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── Scripts ──────────────────────────────────────────────

# script_id 到 tool_type 的映射
SCRIPT_TOOL_MAP = {
    "mission": "narrator",  # 每日简报
    "bounty": "bounty_hunter",  # 赏金猎人
    "alpha": "alpha_radar",  # Alpha 雷达
    "revenue": "revenue_architect",  # 营收架构师
}


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "127.0.0.1"


@app.get("/api/run/{script_id}")
async def run_script(
    script_id: str,
    request: Request,
    visitor_id: str = None,
    token: str = None,  # 通过查询参数传递的 token
):
    """运行脚本（带使用次数检查和扣减）"""
    if script_id not in SCRIPTS:
        raise HTTPException(status_code=404, detail="Unknown script")

    script = SCRIPTS[script_id]
    tool_type = SCRIPT_TOOL_MAP.get(script_id)

    # 检查并扣减使用次数
    try:
        from src.database.connection import get_db
        from src.usage.service import UsageService
        from src.config import settings

        if settings.FEATURE_USER_SYSTEM:
            # 获取数据库会话
            db_gen = get_db()
            db = next(db_gen)
            try:
                # 尝试从请求中获取用户
                user = None
                
                # 优先使用查询参数中的 token
                auth_token = token
                if not auth_token:
                    auth_header = request.headers.get("Authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        auth_token = auth_header.replace("Bearer ", "")
                
                if auth_token:
                    try:
                        from src.auth.utils import verify_token
                        payload = verify_token(auth_token)
                        if payload:
                            from src.database import crud
                            user_id = payload.get("user_id") or payload.get("sub")
                            if user_id:
                                user = crud.get_user_by_id(db, int(user_id))
                    except Exception:
                        pass

                # 获取客户端 IP
                ip_address = get_client_ip(request)

                # 检查使用权限
                service = UsageService(db)
                check_result = service.check_usage(
                    user=user,
                    visitor_id=visitor_id,
                    ip_address=ip_address,
                    tool_type=tool_type,
                )

                if not check_result.get("can_use"):
                    raise HTTPException(
                        status_code=403,
                        detail=check_result.get("message", "无使用权限")
                    )

                # 扣减使用次数
                deduct_result = service.deduct_usage(
                    user=user,
                    visitor_id=visitor_id,
                    ip_address=ip_address,
                    tool_type=tool_type,
                    amount=1,
                )

                if not deduct_result.get("success"):
                    raise HTTPException(
                        status_code=403,
                        detail=deduct_result.get("message", "扣减失败")
                    )

            finally:
                db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"使用次数检查失败，跳过: {e}")

    async def stream():
        proc = await asyncio.create_subprocess_exec(
            "python", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(BASE_DIR),
        )
        running_processes[script_id] = proc
        try:
            async for line in proc.stdout:
                yield f"data: {line.decode('utf-8', errors='replace').rstrip()}\n\n"
            await proc.wait()
            code = proc.returncode
            yield f"data: [DONE] exit={code}\n\n"
        finally:
            running_processes.pop(script_id, None)

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Reports ──────────────────────────────────────────────

@app.get("/api/reports")
def list_reports():
    if not REPORTS_DIR.exists():
        return []
    result = []
    for f in sorted(REPORTS_DIR.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        # 统一使用正斜杠，避免 Windows 路径在 JavaScript 中的转义问题
        rel_path = str(f.relative_to(REPORTS_DIR)).replace("\\", "/")
        result.append({
            "path": rel_path,
            "name": f.name,
            "folder": str(f.parent.relative_to(REPORTS_DIR)).replace("\\", "/"),
            "mtime": f.stat().st_mtime,
        })
    return result

@app.get("/api/reports/content")
def get_report(path: str):
    # 统一路径分隔符，确保 Windows 兼容
    full = REPORTS_DIR / path.replace("\\", "/")
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404)
    return {"content": full.read_text(encoding="utf-8")}


# ── Report Download ───────────────────────────────────────

@app.get("/api/reports/download")
def download_report(path: str, format: str = "md"):
    """单篇报告下载"""
    # 统一路径分隔符，确保 Windows 兼容
    full = REPORTS_DIR / path.replace("\\", "/")
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="报告不存在")
    
    content = full.read_text(encoding="utf-8")
    filename = full.stem  # 文件名（不含扩展名）
    
    if format == "txt":
        # 转换为纯文本：移除 markdown 格式
        import re
        text = content
        # 移除链接，保留文本
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # 移除图片
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
        # 移除粗体/斜体标记
        text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)
        text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
        # 移除代码块标记
        text = re.sub(r'```[\w]*\n?', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 移除水平线
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        content = text.strip()
        
        return Response(
            content=content.encode('utf-8'),
            media_type='text/plain; charset=utf-8',
            headers={"Content-Disposition": f'attachment; filename="{filename}.txt"'}
        )
    else:
        return Response(
            content=content.encode('utf-8'),
            media_type='text/markdown; charset=utf-8',
            headers={"Content-Disposition": f'attachment; filename="{filename}.md"'}
        )


@app.get("/api/reports/batch-download")
def batch_download_reports(paths: str = Query(...), format: str = "md"):
    """批量报告打包下载"""
    path_list = [p.strip() for p in paths.split(",") if p.strip()]
    
    if not path_list:
        raise HTTPException(status_code=400, detail="未选择报告")
    
    # 创建内存中的 zip 文件
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for path in path_list:
            # 统一路径分隔符，确保 Windows 兼容
            full = REPORTS_DIR / path.replace("\\", "/")
            if not full.exists() or not full.is_file():
                continue
            
            content = full.read_text(encoding="utf-8")
            filename = full.stem
            
            if format == "txt":
                # 转换为纯文本
                import re
                text = content
                text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
                text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
                text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)
                text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
                text = re.sub(r'```[\w]*\n?', '', text)
                text = re.sub(r'`([^`]+)`', r'\1', text)
                text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
                text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
                text = re.sub(r'\n{3,}', '\n\n', text)
                content = text.strip()
                
                zip_file.writestr(f"{filename}.txt", content)
            else:
                zip_file.writestr(f"{filename}.md", content)
    
    zip_buffer.seek(0)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type='application/zip',
        headers={"Content-Disposition": f'attachment; filename="reports_{timestamp}.zip"'}
    )


# ── Frontend ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE_DIR / "ui" / "index.html").read_text(encoding="utf-8")


# ── Auth Pages ───────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_page():
    """登录页面"""
    return (BASE_DIR / "ui" / "login.html").read_text(encoding="utf-8")


@app.get("/register", response_class=HTMLResponse)
def register_page():
    """注册页面"""
    return (BASE_DIR / "ui" / "register.html").read_text(encoding="utf-8")


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page():
    """忘记密码页面"""
    return (BASE_DIR / "ui" / "forgot-password.html").read_text(encoding="utf-8")


@app.get("/oauth/callback", response_class=HTMLResponse)
def oauth_callback_page():
    """OAuth 回调页面"""
    return (BASE_DIR / "ui" / "oauth-callback.html").read_text(encoding="utf-8")


@app.get("/account", response_class=HTMLResponse)
def account_page():
    """用户中心页面"""
    return (BASE_DIR / "ui" / "account.html").read_text(encoding="utf-8")


# ── Sources ───────────────────────────────────────────────

SOURCES_META = [
    {"key": "hacker_news", "env_key": "SOURCE_ENABLED_HACKERNEWS", "name": "Hacker News", "icon": "📰", "desc": "热门技术新闻和社区讨论", "requires_key": None},
    {"key": "github_trending", "env_key": "SOURCE_ENABLED_GITHUB_TRENDING", "name": "GitHub Trending", "icon": "⭐", "desc": "GitHub 每日热门仓库", "requires_key": "GITHUB_TOKEN"},
    {"key": "arxiv", "env_key": "SOURCE_ENABLED_ARXIV", "name": "ArXiv AI/ML", "icon": "📄", "desc": "最新 AI/ML 学术论文", "requires_key": None},
    {"key": "producthunt", "env_key": "SOURCE_ENABLED_PRODUCTHUNT", "name": "Product Hunt", "icon": "🚀", "desc": "每日新产品发布", "requires_key": "PRODUCTHUNT_TOKEN"},
    {"key": "v2ex", "env_key": "SOURCE_ENABLED_V2EX", "name": "V2EX", "icon": "💬", "desc": "创意工作者社区", "requires_key": None},
    {"key": "36kr", "env_key": "SOURCE_ENABLED_36KR", "name": "36氪", "icon": "🇨🇳", "desc": "中国科技创业媒体", "requires_key": None},
    {"key": "wallstreet", "env_key": "SOURCE_ENABLED_WALLSTREET", "name": "华尔街见闻", "icon": "📈", "desc": "中国财经资讯", "requires_key": None},
    {"key": "x_grok", "env_key": "SOURCE_ENABLED_X_GROK", "name": "X/Twitter (Grok)", "icon": "🐦", "desc": "X 平台实时搜索（需 Grok）", "requires_key": "XAI_API_KEY"},
    {"key": "hn_blogs", "env_key": "SOURCE_ENABLED_HN_BLOGS", "name": "HN Top Blogs", "icon": "📝", "desc": "Hacker News 热门博客", "requires_key": None},
    {"key": "chrome", "env_key": "SOURCE_ENABLED_CHROME", "name": "Chrome 扩展雷达", "icon": "🔌", "desc": "Chrome 扩展商店趋势", "requires_key": None},
    {"key": "xhs", "env_key": "SOURCE_ENABLED_XHS", "name": "小红书", "icon": "📕", "desc": "小红书热门话题与趋势", "requires_key": None},
    {"key": "tavily", "env_key": "SOURCE_ENABLED_TAVILY", "name": "Tavily 搜索", "icon": "🔍", "desc": "AI 驱动的实时搜索", "requires_key": "TAVILY_TOKEN"},
]

@app.get("/api/sources")
def get_sources():
    """获取所有数据源的状态"""
    env = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
    result = []
    for src in SOURCES_META:
        enabled = env.get(src["env_key"], "true").lower() in ("true", "1", "yes", "on")
        key_configured = True
        if src["requires_key"]:
            key_configured = bool(env.get(src["requires_key"]))
        result.append({
            "key": src["key"],
            "name": src["name"],
            "icon": src["icon"],
            "desc": src["desc"],
            "enabled": enabled,
            "requires_key": src["requires_key"],
            "key_configured": key_configured,
        })
    return result

class SourceUpdate(BaseModel):
    key: str
    enabled: bool

@app.post("/api/sources")
def update_source(body: SourceUpdate):
    """更新数据源开关状态"""
    src = next((s for s in SOURCES_META if s["key"] == body.key), None)
    if not src:
        raise HTTPException(status_code=404, detail="Unknown source")
    ENV_FILE.touch()
    set_key(str(ENV_FILE), src["env_key"], "true" if body.enabled else "false")
    return {"ok": True}


# ── Tavily Keywords ────────────────────────────────────────

class TavilyKeywords(BaseModel):
    keywords: str

@app.get("/api/tavily-keywords")
def get_tavily_keywords():
    """获取Tavily自定义关键词"""
    env = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
    keywords = env.get("TAVILY_CUSTOM_KEYWORDS", "")
    return {"keywords": keywords}

@app.post("/api/tavily-keywords")
def save_tavily_keywords(body: TavilyKeywords):
    """保存Tavily自定义关键词"""
    ENV_FILE.touch()
    set_key(str(ENV_FILE), "TAVILY_CUSTOM_KEYWORDS", body.keywords)
    return {"ok": True}


# ── Static Files ─────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "ui" / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8680"))
    uvicorn.run(app, host="0.0.0.0", port=port)