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
    version="2.1.0",
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

# 自部署模式控制（环境变量）
import os
SELF_HOSTED = os.getenv("SELF_HOSTED", "").lower() in ("true", "1", "yes", "on")

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


# ── Register Activation Router ────────────────────────────────────
# v2.1 激活码架构：替代原有的 auth_router 和 user_router

try:
    from src.activation.router import router as activation_router
    app.include_router(activation_router, prefix="/api/activation", tags=["激活码"])
    logger.info("激活码路由注册成功")
except ImportError as e:
    logger.warning(f"激活码路由注册失败: {e}")


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


# ── Register Marketplace Router ───────────────────────────────

try:
    from src.marketplace.router import router as marketplace_router
    app.include_router(marketplace_router, prefix="/api/marketplace", tags=["预设广场"])
    logger.info("预设广场路由注册成功")
except ImportError as e:
    logger.warning(f"预设广场路由注册失败: {e}")


# ── Register Admin Router ───────────────────────────────

try:
    from src.admin.router import router as admin_router
    app.include_router(admin_router, prefix="/api/admin", tags=["管理员"])
    logger.info("管理员路由注册成功")
except ImportError as e:
    logger.warning(f"管理员路由注册失败: {e}")


# ── Register Monitoring Router ───────────────────────────────

try:
    from src.monitoring.router import router as monitoring_router
    app.include_router(monitoring_router, prefix="/api/monitoring", tags=["监控"])
    logger.info("监控路由注册成功")
except ImportError as e:
    logger.warning(f"监控路由注册失败: {e}")


# ── Register Source Health Router ───────────────────────────────

try:
    from src.sensors.source_health import create_health_router
    health_router = create_health_router()
    app.include_router(health_router, tags=["数据源健康"])
    logger.info("数据源健康路由注册成功")
except ImportError as e:
    logger.warning(f"数据源健康路由注册失败: {e}")


# ── Register Payment Router ───────────────────────────────

try:
    from src.payment import payment_router
    app.include_router(payment_router, prefix="/api/payment", tags=["支付"])
    logger.info("支付路由注册成功")
except ImportError as e:
    logger.warning(f"支付路由注册失败: {e}")


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
    """
    获取配置（官方托管版返回空对象，防止 API Key 泄露）
    
    自部署用户（SELF_HOSTED=true）：可返回 .env 配置作为默认值
    """
    if SELF_HOSTED:
        # 自部署模式：返回 .env 配置（可选的默认值）
        if not ENV_FILE.exists():
            return {}
        return dict(dotenv_values(ENV_FILE))
    else:
        # 官方托管版：不返回敏感配置
        return {}

@app.post("/api/config")
def save_config(body: EnvUpdate):
    """
    保存配置到 .env 文件
    
    自部署用户（SELF_HOSTED=true）：允许通过 Web UI 保存配置
    官方托管版：禁用，返回 403（配置仅保存在浏览器 localStorage）
    """
    if not SELF_HOSTED:
        # 官方托管版：禁止写入服务器配置
        raise HTTPException(
            status_code=403,
            detail="官方托管版不支持服务器保存配置，请使用浏览器本地存储"
        )
    
    # 自部署模式：允许写入 .env
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


# 敏感Key列表（需要base64解码）
SENSITIVE_CONFIG_KEYS = [
    'LLM_API_KEY', 'XAI_API_KEY', 'GITHUB_TOKEN',
    'TAVILY_TOKEN', 'PRODUCTHUNT_TOKEN', 'TRANSLATOR_API_KEY'
]


def _decode_sensitive_key(value: str, key: str) -> str:
    """解码敏感Key（前端base64编码）"""
    import base64
    if key in SENSITIVE_CONFIG_KEYS and value:
        try:
            return base64.b64decode(value).decode('utf-8')
        except Exception:
            # 如果解码失败，可能是未编码的值（兼容旧版）
            return value
    return value


@app.get("/api/run/{script_id}")
async def run_script(
    script_id: str,
    request: Request,
    device_id: str = None,
    visitor_id: str = None,
    # 用户配置参数（前端传入）
    LLM_API_KEY: str = None,
    LLM_BASE_URL: str = None,
    LLM_MODEL: str = None,
    LLM_API_FORMAT: str = None,
    XAI_API_KEY: str = None,
    XAI_BASE_URL: str = None,
    XAI_MODEL: str = None,
    GITHUB_TOKEN: str = None,
    TAVILY_TOKEN: str = None,
    PRODUCTHUNT_TOKEN: str = None,
    TRANSLATOR_API_KEY: str = None,
    TRANSLATOR_BASE_URL: str = None,
    TRANSLATOR_MODEL: str = None,
):
    """
    运行脚本（带使用次数检查和扣减）

    v2.1 激活码架构：
    - device_id: 已激活用户设备 ID
    - visitor_id: 匿名用户访客 ID
    - 通过环境变量传给子进程
    - 支持用户隔离（code_id 替代 user_id）
    """
    if script_id not in SCRIPTS:
        raise HTTPException(status_code=404, detail="Unknown script")

    script = SCRIPTS[script_id]
    tool_type = SCRIPT_TOOL_MAP.get(script_id)

    # 用户身份（用于报告隔离）
    code_id_for_env = None

    # 检查并扣减使用次数
    try:
        from src.database.connection import get_db
        from src.usage.service import UsageService

        # 获取数据库会话
        db_gen = get_db()
        db = next(db_gen)
        try:
            # v2.1 激活码架构：使用新的 UsageService
            service = UsageService(db)

            # 检查使用权限
            check_result = service.check_usage(
                device_id=device_id,
                visitor_id=visitor_id,
                tool_type=tool_type,
            )

            if not check_result.get("can_use"):
                raise HTTPException(
                    status_code=403,
                    detail=check_result.get("message", "无使用权限")
                )

            # 扣减使用次数
            consume_result = service.consume(
                device_id=device_id,
                visitor_id=visitor_id,
                tool_type=tool_type,
                amount=1,
            )

            if not consume_result.get("success"):
                raise HTTPException(
                    status_code=403,
                    detail=consume_result.get("message", "扣减失败")
                )

            # 确定报告目录标识
            if device_id:
                # 已激活用户：使用 code_id
                from src.database import crud
                activation_code = crud.get_activation_code_by_device_id(db, device_id)
                if activation_code:
                    code_id_for_env = f"code_{activation_code.id}"
            elif visitor_id:
                # 匿名用户
                code_id_for_env = f"anon_{visitor_id}"

        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"使用次数检查失败: {e}")
        # 返回错误响应，而不是跳过检查
        async def error_stream():
            yield f"data: [ERROR] 服务暂时不可用，请稍后重试\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def stream():
        # 构建用户专属环境变量
        env = os.environ.copy()

        # 传递用户ID（用于报告隔离）v2.1: code_id 替代 user_id
        if code_id_for_env:
            env["USER_ID"] = code_id_for_env
        
        # 传递用户配置（敏感Key需要解码）
        config_mapping = {
            'LLM_API_KEY': 'USER_LLM_API_KEY',
            'LLM_BASE_URL': 'USER_LLM_BASE_URL',
            'LLM_MODEL': 'USER_LLM_MODEL',
            'LLM_API_FORMAT': 'USER_LLM_API_FORMAT',
            'XAI_API_KEY': 'USER_XAI_API_KEY',
            'XAI_BASE_URL': 'USER_XAI_BASE_URL',
            'XAI_MODEL': 'USER_XAI_MODEL',
            'GITHUB_TOKEN': 'USER_GITHUB_TOKEN',
            'TAVILY_TOKEN': 'USER_TAVILY_TOKEN',
            'PRODUCTHUNT_TOKEN': 'USER_PRODUCTHUNT_TOKEN',
            'TRANSLATOR_API_KEY': 'USER_TRANSLATOR_API_KEY',
            'TRANSLATOR_BASE_URL': 'USER_TRANSLATOR_BASE_URL',
            'TRANSLATOR_MODEL': 'USER_TRANSLATOR_MODEL',
        }
        
        # 获取所有传入的配置参数
        config_values = {
            'LLM_API_KEY': LLM_API_KEY,
            'LLM_BASE_URL': LLM_BASE_URL,
            'LLM_MODEL': LLM_MODEL,
            'LLM_API_FORMAT': LLM_API_FORMAT,
            'XAI_API_KEY': XAI_API_KEY,
            'XAI_BASE_URL': XAI_BASE_URL,
            'XAI_MODEL': XAI_MODEL,
            'GITHUB_TOKEN': GITHUB_TOKEN,
            'TAVILY_TOKEN': TAVILY_TOKEN,
            'PRODUCTHUNT_TOKEN': PRODUCTHUNT_TOKEN,
            'TRANSLATOR_API_KEY': TRANSLATOR_API_KEY,
            'TRANSLATOR_BASE_URL': TRANSLATOR_BASE_URL,
            'TRANSLATOR_MODEL': TRANSLATOR_MODEL,
        }
        
        # 设置环境变量
        for src_key, env_key in config_mapping.items():
            value = config_values.get(src_key)
            if value:
                # 敏感Key需要base64解码
                decoded_value = _decode_sensitive_key(value, src_key)
                env[env_key] = decoded_value
        
        # 启动子进程
        proc = await asyncio.create_subprocess_exec(
            "python", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(BASE_DIR),
            env=env,  # 传入用户专属环境变量
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

def _get_code_id_from_device(device_id: str = None) -> str:
    """从 device_id 获取激活码 ID，用于报告目录隔离"""
    if not device_id:
        return None
    try:
        from src.database.connection import get_db
        from src.database import crud
        db_gen = get_db()
        db = next(db_gen)
        try:
            activation_code = crud.get_activation_code_by_device_id(db, device_id)
            if activation_code:
                return f"code_{activation_code.id}"
        finally:
            db.close()
    except Exception:
        pass
    return None


def _get_report_dir(device_id: str = None, visitor_id: str = None):
    """
    获取报告目录路径
    - 有 device_id → 查询 code_id → code_{id}
    - 有 visitor_id → anon_{visitor_id}
    - 否则返回 None
    """
    if device_id:
        code_dir = _get_code_id_from_device(device_id)
        if code_dir:
            return REPORTS_DIR / code_dir
    if visitor_id:
        return REPORTS_DIR / f"anon_{visitor_id}"
    return None

@app.get("/api/reports")
def list_reports(
    request: Request,
    device_id: str = None,
    visitor_id: str = None,
):
    """
    获取报告列表，根据用户身份隔离目录
    v2.1 使用激活码架构，通过 device_id 查询 code_id 来隔离报告
    """
    # 获取报告目录
    user_report_dir = _get_report_dir(device_id=device_id, visitor_id=visitor_id)

    # 没有有效身份则返回空列表
    if not user_report_dir:
        return []

    if not user_report_dir.exists():
        return []
    
    result = []
    for f in sorted(user_report_dir.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        # 统一使用正斜杠，避免 Windows 路径在 JavaScript 中的转义问题
        rel_path = str(f.relative_to(user_report_dir)).replace("\\", "/")
        result.append({
            "path": rel_path,
            "name": f.name,
            "folder": str(f.parent.relative_to(user_report_dir)).replace("\\", "/"),
            "mtime": f.stat().st_mtime,
        })
    return result

@app.get("/api/reports/content")
def get_report(
    path: str,
    request: Request,
    device_id: str = None,
    visitor_id: str = None,
):
    """
    获取报告内容，根据用户身份隔离目录
    v2.1 通过 device_id 获取 code_id 来隔离报告
    """
    # 获取报告目录
    user_report_dir = _get_report_dir(device_id=device_id, visitor_id=visitor_id)

    if not user_report_dir:
        raise HTTPException(status_code=403, detail="无法识别用户")

    # 安全检查：确保路径不会跳出用户报告目录
    full = user_report_dir / path.replace("\\", "/")
    try:
        full = full.resolve()
        user_report_dir = user_report_dir.resolve()
        if not str(full).startswith(str(user_report_dir)):
            raise HTTPException(status_code=403, detail="禁止访问其他用户的报告")
    except Exception:
        raise HTTPException(status_code=403, detail="无效路径")

    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404)
    return {"content": full.read_text(encoding="utf-8")}


# ── Report Download ───────────────────────────────────────

@app.get("/api/reports/download")
def download_report(
    path: str,
    request: Request,
    device_id: str = None,
    visitor_id: str = None,
    format: str = "md",
):
    """下载报告文件，根据用户身份隔离目录"""
    # 获取报告目录
    user_report_dir = _get_report_dir(device_id=device_id, visitor_id=visitor_id)

    if not user_report_dir:
        raise HTTPException(status_code=403, detail="无法识别用户")

    # 安全检查：确保路径不会跳出用户报告目录
    full = user_report_dir / path.replace("\\", "/")
    try:
        full = full.resolve()
        user_report_dir = user_report_dir.resolve()
        if not str(full).startswith(str(user_report_dir)):
            raise HTTPException(status_code=403, detail="禁止访问其他用户的报告")
    except Exception:
        raise HTTPException(status_code=403, detail="无效路径")

    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="报告文件不存在")

    content_text = full.read_text(encoding="utf-8")
    filename = full.stem

    if format == "txt":
        # 转换为纯文本：移除 markdown 格式
        import re
        text = content_text
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
        content_text = text.strip()
        
        return Response(
            content=content_text.encode('utf-8'),
            media_type='text/plain; charset=utf-8',
            headers={"Content-Disposition": f'attachment; filename="{filename}.txt"'}
        )
    else:
        return Response(
            content=content_text.encode('utf-8'),
            media_type='text/markdown; charset=utf-8',
            headers={"Content-Disposition": f'attachment; filename="{filename}.md"'}
        )

@app.get("/api/reports/batch-download")
@app.get("/api/reports/batch-download")
def batch_download_reports(
    request: Request,
    paths: str = Query(...),
    device_id: str = None,
    visitor_id: str = None,
    format: str = "md",
):
    """批量下载多个报告为 zip，根据用户身份隔离目录"""
    # 获取报告目录
    user_report_dir = _get_report_dir(device_id=device_id, visitor_id=visitor_id)

    if not user_report_dir:
        raise HTTPException(status_code=403, detail="无法识别用户")

    # 安全检查：确保所有路径都在用户报告目录内
    user_report_dir = user_report_dir.resolve()

    path_list = [p.strip() for p in paths.split(",") if p.strip()]

    if not path_list:
        raise HTTPException(status_code=400, detail="未选择报告")

    # 创建内存中的 zip 文件
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for path in path_list:
            # 安全检查：防止路径遍历攻击
            full = user_report_dir / path.replace("\\", "/")
            try:
                full = full.resolve()
                if not str(full).startswith(str(user_report_dir)):
                    continue  # 跳过非法路径
            except Exception:
                continue
            
            if not full.exists() or not full.is_file():
                continue
            
            content_text = full.read_text(encoding="utf-8")
            filename = full.stem
            
            if format == "txt":
                # 转换为纯文本
                import re
                text = content_text
                text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
                text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
                text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)
                text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
                text = re.sub(r'```[\w]*\n?', '', text)
                text = re.sub(r'`([^`]+)`', r'\1', text)
                text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
                text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
                text = re.sub(r'\n{3,}', '\n\n', text)
                content_text = text.strip()
                
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


# ── Admin Page ───────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    """管理后台页面"""
    return (BASE_DIR / "ui" / "admin.html").read_text(encoding="utf-8")


# ── Sources ───────────────────────────────────────────────

SOURCES_META = [
    {"key": "hacker_news", "env_key": "SOURCE_ENABLED_HACKERNEWS", "name": "Hacker News", "icon": "📰", "desc": "热门技术新闻和社区讨论", "requires_key": None},
    {"key": "github_trending", "env_key": "SOURCE_ENABLED_GITHUB_TRENDING", "name": "GitHub Trending", "icon": "⭐", "desc": "GitHub 每日热门仓库", "requires_key": "GITHUB_TOKEN"},
    {"key": "arxiv", "env_key": "SOURCE_ENABLED_ARXIV", "name": "ArXiv AI/ML", "icon": "📄", "desc": "最新 AI/ML 学术论文", "requires_key": None},
    {"key": "producthunt", "env_key": "SOURCE_ENABLED_PRODUCTHUNT", "name": "Product Hunt", "icon": "🚀", "desc": "每日新产品发布", "requires_key": "PRODUCTHUNT_TOKEN"},
    {"key": "v2ex", "env_key": "SOURCE_ENABLED_V2EX", "name": "V2EX", "icon": "💬", "desc": "创意工作者社区", "requires_key": None},
    {"key": "36kr", "env_key": "SOURCE_ENABLED_36KR", "name": "36氪", "icon": "🇨🇳", "desc": "中国科技创业媒体", "requires_key": None},
    {"key": "wallstreet", "env_key": "SOURCE_ENABLED_WALLSTREET", "name": "华尔街见闻", "icon": "📈", "desc": "中国财经资讯", "requires_key": None},
    {"key": "hn_blogs", "env_key": "SOURCE_ENABLED_HN_BLOGS", "name": "HN Top Blogs", "icon": "📝", "desc": "Hacker News 热门博客", "requires_key": None},
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