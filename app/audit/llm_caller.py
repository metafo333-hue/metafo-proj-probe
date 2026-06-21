"""audit/llm_caller.py · 闸级 LLM 调用包装器。

独立于 app.services.llm（probe 业务 LLM），此模块专供 audit 闸（闸2/3/5/6）调用，
使用独立的环境变量配置，降级策略与 probe LLM 层解耦。

环境变量
--------
LITELLM_BASE_URL  : OpenAI 兼容端点 base（如 http://ufo2:4000/v1）
LITELLM_API_KEY   : 鉴权 key
LITELLM_MODEL     : 国产模型别名（如 bl-glm/bl-qwen/deepseek·禁 cc-*/claude/gpt·见 foundation-constraints 铁律一）

切换控制
--------
GATES_LIVE_MODEL=1  → 启用真实 LLM 调用（闸2/3/5/6 有真判断）
GATES_LIVE_MODEL=0  → 保持 StubBackend 行为（默认）

降级策略
--------
任何网络异常 / 超时 / 解析失败 → 返回 None，调用方回退 stub 中性值，不抛异常。

注意
----
⚠️ 真模型未在生产实测，需 probe-a 部署后验证。
   本地开发、CI 环境未设 LITELLM_BASE_URL / LITELLM_API_KEY 时，
   call() 恒返回 None，闸行为与 GATES_LIVE_MODEL=0 完全一致。
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ── 配置（仅从环境变量读，禁硬编码值）─────────────────────────────────────────
# 键名对齐 probe-a 现有 env(PROBE_LITELLM_BASE/KEY·ufo2 LiteLLM)，fallback LITELLM_*(本地/CI 兼容)
_BASE_URL = os.getenv("PROBE_LITELLM_BASE") or os.getenv("LITELLM_BASE_URL", "")
_API_KEY  = os.getenv("PROBE_LITELLM_KEY") or os.getenv("LITELLM_API_KEY", "")
_MODEL    = os.getenv("GATES_LITELLM_MODEL") or os.getenv("LITELLM_MODEL", "bl-glm")
_TIMEOUT  = 10  # 秒；闸级调用比业务层更短，防止 pipeline 阻塞


def is_enabled() -> bool:
    """GATES_LIVE_MODEL=1 且有 API 端点和 key 时返回 True。"""
    return (
        os.getenv("GATES_LIVE_MODEL", "0") == "1"
        and bool(_BASE_URL)
        and bool(_API_KEY)
    )


def call(
    messages: list[dict[str, str]],
    max_tokens: int = 100,
) -> Optional[str]:
    """向 LiteLLM/OpenAI 兼容端点发起同步 chat 请求。

    Parameters
    ----------
    messages   : OpenAI messages 格式列表 [{"role": "user", "content": "..."}]
    max_tokens : 最大输出 token（闸级调用保持小值，降低延迟）

    Returns
    -------
    str  : 模型回复文本（stripped）
    None : 调用失败（网络 / 超时 / 格式异常）；调用方应回退 stub 值
    """
    base = _BASE_URL
    key  = _API_KEY
    if not base or not key:
        return None

    try:
        r = httpx.post(
            f"{base.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       _MODEL,
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": 0,
            },
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            body = r.json()
            return body["choices"][0]["message"]["content"].strip()
        logger.warning(
            "audit llm_caller: HTTP %s from %s", r.status_code, base
        )
        return None
    except Exception as exc:
        logger.warning("audit llm_caller: 调用失败（%s: %s）→ 降级 stub", type(exc).__name__, exc)
        return None
