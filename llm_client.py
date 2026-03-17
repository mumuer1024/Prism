"""
统一 LLM 客户端 - 支持 OpenAI 兼容 / Gemini 原生 / Claude 原生 三种格式
使用方式：读取 .env 中的配置，自动选择对应的请求格式
"""
import httpx
import logging

logger = logging.getLogger(__name__)


def _detect_format(base_url: str, api_format: str = None) -> str:
    """
    自动检测或返回指定的 API 格式。
    优先使用显式指定的 api_format，否则根据 URL 推断。
    """
    if api_format:
        return api_format.lower()
    url = base_url.lower()
    if "anthropic.com" in url or "/v1/messages" in url:
        return "claude"
    if "generativelanguage.googleapis.com" in url or "generatecontent" in url:
        return "gemini"
    return "openai"


def chat(
    prompt: str,
    system: str = "",
    base_url: str = "",
    api_key: str = "",
    model: str = "",
    api_format: str = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    timeout: int = 60,
) -> str:
    """
    统一聊天接口。自动根据格式发送请求，返回纯文本回复。

    Args:
        prompt: 用户消息
        system: 系统提示（可选）
        base_url: API 基础地址
        api_key: API 密钥
        model: 模型名称
        api_format: 强制指定格式 'openai' | 'gemini' | 'claude'，None 则自动检测
        temperature: 温度
        max_tokens: 最大 token 数
        timeout: 超时秒数

    Returns:
        模型回复文本，失败时返回空字符串
    """
    fmt = _detect_format(base_url, api_format)

    try:
        if fmt == "gemini":
            return _chat_gemini(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout)
        elif fmt == "claude":
            return _chat_claude(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout)
        else:
            return _chat_openai(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout)
    except Exception as e:
        logger.error(f"LLM 调用失败 [{fmt}]: {e}")
        return ""


# ── OpenAI 兼容 ──────────────────────────────────────────────────────────────

def _chat_openai(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout):
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        # 兼容只填了 base url 的情况
        if "/v1" not in url:
            url = url + "/v1/chat/completions"
        else:
            url = url.rstrip("/v1").rstrip("/") + "/v1/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


# ── Gemini 原生 ──────────────────────────────────────────────────────────────

def _chat_gemini(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout):
    # 支持两种 URL 写法：
    # 1. https://generativelanguage.googleapis.com/v1beta/models  (原生)
    # 2. 任意兼容 OpenAI 的中转站 → 走 openai 格式
    base = base_url.rstrip("/")
    if "generativelanguage.googleapis.com" in base:
        url = f"{base}/{model}:generateContent?key={api_key}"
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
            contents.append({"role": "model", "parts": [{"text": "好的，我明白了。"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    else:
        # 中转站走 OpenAI 兼容格式
        return _chat_openai(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout)


# ── Claude 原生 ──────────────────────────────────────────────────────────────

def _chat_claude(prompt, system, base_url, api_key, model, temperature, max_tokens, timeout):
    base = base_url.rstrip("/")
    if base.endswith("/messages"):
        url = base
    elif "/v1" in base:
        url = base.rstrip("/") + "/messages"
    else:
        url = base + "/v1/messages"

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload, headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        })
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()


# ── 模型列表拉取（供 UI 使用）────────────────────────────────────────────────

def list_models(base_url: str, api_key: str, api_format: str = None) -> list[str]:
    """
    拉取模型列表。Gemini 原生 / Claude 原生均走各自接口，OpenAI 兼容走 /v1/models。
    """
    fmt = _detect_format(base_url, api_format)

    try:
        if fmt == "gemini" and "generativelanguage.googleapis.com" in base_url:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            with httpx.Client(timeout=10) as client:
                r = client.get(url)
                r.raise_for_status()
                return [m["name"].split("/")[-1] for m in r.json().get("models", [])]

        elif fmt == "claude" and "anthropic.com" in base_url:
            # Anthropic 没有公开模型列表 API，返回常用模型
            return [
                "claude-opus-4-5",
                "claude-sonnet-4-5",
                "claude-haiku-4-5",
                "claude-sonnet-4-20250514",
            ]

        else:
            # OpenAI 兼容
            url = base_url.rstrip("/")
            if "/chat/completions" in url:
                url = url.split("/chat/completions")[0]
            if not url.endswith("/models"):
                if "/v1" not in url:
                    url = url + "/v1/models"
                else:
                    url = url.rstrip("/") + "/models"

            with httpx.Client(timeout=10) as client:
                r = client.get(url, headers={"Authorization": f"Bearer {api_key}"})
                r.raise_for_status()
                return sorted([m["id"] for m in r.json().get("data", [])])

    except Exception as e:
        logger.error(f"拉取模型列表失败: {e}")
        raise
