# -*- coding: utf-8 -*-
"""
Grok API 调用传感器（优化版）

功能：
- 重试机制（tenacity）
- 连接复用（httpx.Client）
- 结构化错误处理
- 批量舆情核查支持
- 请求日志记录

v2.1 改造：优先读取用户传入的 XAI Key（USER_* 环境变量）
"""

import os
import sys
import datetime
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Force UTF-8 stdout for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 配置日志
logger = logging.getLogger(__name__)


def get_user_xai_config():
    """
    获取 XAI 配置（优先用户传入，回退全局 .env）
    
    Returns:
        dict: XAI 配置字典
    """
    return {
        'api_key': os.getenv("USER_XAI_API_KEY") or os.getenv("XAI_API_KEY", ""),
        'base_url': os.getenv("USER_XAI_BASE_URL") or os.getenv("XAI_BASE_URL", "https://api.x.ai/v1/chat/completions"),
        'model': os.getenv("USER_XAI_MODEL") or os.getenv("XAI_MODEL", "grok-3"),
        'timeout': int(os.getenv("GROK_TIMEOUT", "60")),
    }


# 默认配置（用于类初始化）
try:
    from config import GROK_TIMEOUT
except ImportError:
    GROK_TIMEOUT = int(os.getenv("GROK_TIMEOUT", "60"))


@dataclass
class GrokResponse:
    """Grok API 响应结构"""
    success: bool
    content: str
    error: Optional[str] = None
    tokens_used: int = 0
    response_time_ms: int = 0
    model: str = ""


class GrokSensor:
    """
    Grok API 调用传感器

    优化特性：
    - 连接复用：使用 httpx.Client 作为类成员
    - 重试机制：网络错误自动重试 3 次
    - 结构化响应：返回 GrokResponse 对象
    - 批量支持：支持多产品合并调用
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        timeout: int = None,
    ):
        # 优先读取用户传入的配置
        user_config = get_user_xai_config()
        self.api_key = api_key or user_config['api_key']
        self.base_url = base_url or user_config['base_url']
        self.model = model or user_config['model']
        self.timeout = timeout or user_config['timeout']

        # 创建复用的 HTTP 客户端
        self._client = httpx.Client(timeout=self.timeout)

        logger.info(f"GrokSensor 初始化: model={self.model}, timeout={self.timeout}s")

    def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            self._client.close()
            logger.info("GrokSensor HTTP 客户端已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except:
            pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
        reraise=True,
    )
    def _call_api(
        self,
        system_content: str,
        user_content: str,
        temperature: float = 0.5,
    ) -> Dict:
        """
        调用 Grok API（带重试）

        Args:
            system_content: 系统消息
            user_content: 用户消息
            temperature: 温度参数

        Returns:
            API 响应 JSON
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "stream": False,
            "temperature": temperature
        }

        start_time = datetime.datetime.now()

        response = self._client.post(
            self.base_url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        elapsed_ms = int((datetime.datetime.now() - start_time).total_seconds() * 1000)

        data = response.json()

        # 记录请求日志
        tokens_used = data.get('usage', {}).get('total_tokens', 0)
        logger.info(
            f"Grok API 调用成功: model={self.model}, "
            f"tokens={tokens_used}, time={elapsed_ms}ms"
        )

        return {
            "data": data,
            "elapsed_ms": elapsed_ms,
            "tokens_used": tokens_used,
        }

    def fetch_intel(
        self,
        query: str,
        override_prompt: str = None,
        temperature: float = 0.5,
    ) -> GrokResponse:
        """
        获取情报（单个查询）

        Args:
            query: 搜索关键词
            override_prompt: 自定义 Prompt（完全覆盖默认）
            temperature: 温度参数

        Returns:
            GrokResponse 结构化响应
        """
        if not self.api_key:
            logger.error("XAI API Key 未配置（请在配置页填写 XAI API Key）")
            return GrokResponse(
                success=False,
                content="",
                error="API Key 未配置，请在配置页填写 XAI API Key",
            )

        logger.info(f"Grok Sensor: 开始查询 '{query}'")

        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        year_str = datetime.datetime.now().strftime("%Y")

        if override_prompt:
            system_content = f"You are a specialized Data Analyst. Current Date: {today_str}. Follow the user's instructions strictly."
            user_content = override_prompt
        else:
            system_content = self._build_default_system_prompt(today_str, year_str)
            user_content = f"Search X for the latest trends about '{query}' happened in {year_str}. Focus on specific recent events. Reply in Chinese. Follow the output format strictly."

        try:
            result = self._call_api(system_content, user_content, temperature)
            content = result["data"]["choices"][0]["message"]["content"]

            print("\n" + "=" * 60)
            print(f"  🦅 Grok Intelligence Report: {query}")
            print("=" * 60 + "\n")
            print(content)

            return GrokResponse(
                success=True,
                content=content,
                tokens_used=result["tokens_used"],
                response_time_ms=result["elapsed_ms"],
                model=self.model,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"API 错误: {e.response.status_code} - {e.response.text[:200]}"
            logger.error(error_msg)
            return GrokResponse(success=False, content="", error=error_msg)

        except (httpx.NetworkError, httpx.TimeoutException) as e:
            error_msg = f"网络错误: {str(e)}"
            logger.error(error_msg)
            return GrokResponse(success=False, content="", error=error_msg)

        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg)
            return GrokResponse(success=False, content="", error=error_msg)

    def batch_fetch_intel(
        self,
        items: List[Dict[str, str]],
        context: str = "产品舆情核查",
    ) -> Dict[str, GrokResponse]:
        """
        批量获取情报（合并调用）

        将多个查询合并为一次 API 调用，减少请求次数。

        Args:
            items: 查询项列表，每项包含 {"name": str, "description": str}
            context: 上下文描述

        Returns:
            Dict[name, GrokResponse] 各项的响应结果
        """
        if not self.api_key:
            return {"_error": GrokResponse(success=False, content="", error="API Key 未配置")}

        if not items:
            return {}

        logger.info(f"Grok Sensor: 批量查询 {len(items)} 个项目")

        today_str = datetime.datetime.now().strftime("%Y-%m-%d")

        # 构建批量查询 Prompt
        items_text = "\n".join([
            f"{i+1}. **{item['name']}**: {item.get('description', '无描述')}"
            for i, item in enumerate(items)
        ])

        system_content = (
            f"You are a Commercial Intelligence Analyst. Current Date: {today_str}. "
            "**IMPORTANT: You must answer in Simplified Chinese (简体中文).**\n\n"
            "**⚠️ 输出格式要求（必须严格遵守）：**\n"
            "为每个产品单独输出一个舆情分析段落，格式如下：\n"
            "### [产品名称]\n"
            "- 舆情概述：...\n"
            "- 用户评价：...\n"
            "- 潜在风险：...\n"
            "- 建议：...\n\n"
            "每个产品之间用空行分隔。禁止输出其他内容。"
        )

        user_content = (
            f"请对以下 {len(items)} 个产品进行舆情核查分析：\n\n"
            f"{items_text}\n\n"
            f"分析要求：\n"
            f"1. 搜索每个产品在社交媒体上的最新讨论\n"
            f"2. 分析用户评价和潜在风险\n"
            f"3. 提供简要建议\n"
            f"请严格按照格式输出，每个产品单独一段。"
        )

        try:
            result = self._call_api(system_content, user_content, temperature=0.3)
            full_content = result["data"]["choices"][0]["message"]["content"]

            # 解析各产品的结果
            responses = self._parse_batch_response(full_content, items)

            logger.info(f"批量查询完成: {len(responses)} 个产品")

            return responses

        except Exception as e:
            error_msg = f"批量查询错误: {str(e)}"
            logger.error(error_msg)
            return {
                "_error": GrokResponse(success=False, content="", error=error_msg)
            }

    def _parse_batch_response(
        self,
        content: str,
        items: List[Dict[str, str]],
    ) -> Dict[str, GrokResponse]:
        """
        解析批量响应内容

        Args:
            content: API 返回的完整内容
            items: 查询项列表

        Returns:
            各项的响应字典
        """
        responses = {}

        # 按产品名称分割内容
        for item in items:
            name = item['name']
            # 查找该产品的段落
            pattern = f"### {name}"
            if pattern in content:
                # 提取该产品的段落
                start = content.find(pattern)
                # 查找下一个产品的开始位置
                next_start = len(content)
                for other_item in items:
                    other_pattern = f"### {other_item['name']}"
                    other_pos = content.find(other_pattern, start + len(pattern))
                    if other_pos > start and other_pos < next_start:
                        next_start = other_pos

                item_content = content[start:next_start].strip()
                responses[name] = GrokResponse(
                    success=True,
                    content=item_content,
                    model=self.model,
                )
            else:
                # 未找到该产品的段落
                responses[name] = GrokResponse(
                    success=False,
                    content="",
                    error=f"未找到 {name} 的分析结果",
                )

        return responses

    def _build_default_system_prompt(self, today_str: str, year_str: str) -> str:
        """构建默认系统 Prompt"""
        return (
            f"You are a Commercial Intelligence Analyst. **CURRENT DATE: {today_str}**. "
            "Your goal is to find high-signal discussions from the **LAST 24 HOURS ONLY**. "
            f"❌ CRITICAL RULE: Do NOT report events from {int(year_str)-2} or {int(year_str)-1} as 'new'. "
            "If the trend is from 2024/2025, explicitly label it as 'Historical Context'. "
            "**IMPORTANT: You must answer in Simplified Chinese (简体中文).**\n\n"
            "**⚠️ 输出格式要求（必须严格遵守）：**\n"
            f"1. 第一行必须是：**商业情报快报 | {today_str}（过去24小时高信号X讨论）**\n"
            "2. 空一行后，先写一段简短的总览（2-3句话）\n"
            "3. 然后用编号列表列出具体事件，每条包含：事件标题、关键账号、核心发现\n"
            "4. 最后用一段话总结趋势洞察\n"
            "5. 禁止在开头写'作为商业情报分析师'等废话，直接输出内容"
        )


# ==========================================
# 兼容旧版 API 的函数
# ==========================================

_sensor_instance: Optional[GrokSensor] = None


def get_sensor() -> GrokSensor:
    """获取全局 GrokSensor 实例"""
    global _sensor_instance
    if _sensor_instance is None:
        _sensor_instance = GrokSensor()
    return _sensor_instance


def fetch_grok_intel(query: str, override_prompt: str = None) -> str:
    """
    获取情报（兼容旧版 API）

    Args:
        query: 搜索关键词
        override_prompt: 自定义 Prompt

    Returns:
        情报内容字符串（错误时返回 "Error: ..."）
    """
    sensor = get_sensor()
    response = sensor.fetch_intel(query, override_prompt)

    if response.success:
        return response.content
    else:
        return f"Error: {response.error}"


def batch_fetch_grok_intel(items: List[Dict[str, str]]) -> Dict[str, str]:
    """
    批量获取情报（兼容旧版 API）

    Args:
        items: 查询项列表

    Returns:
        Dict[name, content] 各项的内容
    """
    sensor = get_sensor()
    responses = sensor.batch_fetch_intel(items)

    result = {}
    for name, resp in responses.items():
        if resp.success:
            result[name] = resp.content
        else:
            result[name] = f"Error: {resp.error}"

    return result


# ==========================================
# CLI 入口
# ==========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Grok API 调用传感器")
    parser.add_argument("query", nargs="?", help="搜索关键词")
    parser.add_argument("--batch", nargs="+", help="批量查询（多个产品名称）")
    parser.add_argument("--prompt", help="自定义 Prompt")
    parser.add_argument("--model", default="grok-3", help="模型名称")

    args = parser.parse_args()

    with GrokSensor(model=args.model) as sensor:
        if args.batch:
            # 批量查询
            items = [{"name": name, "description": ""} for name in args.batch]
            results = sensor.batch_fetch_intel(items)
            for name, resp in results.items():
                print(f"\n{'='*60}")
                print(f"  {name}")
                print("=" * 60)
                if resp.success:
                    print(resp.content)
                else:
                    print(f"❌ {resp.error}")
        elif args.query:
            # 单个查询
            resp = sensor.fetch_intel(args.query, args.prompt)
            if not resp.success:
                print(f"❌ {resp.error}")
        else:
            parser.print_help()