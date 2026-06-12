"""AnySearch 联网搜索适配器 · 免费 1000次/天 · 无需 key。

用途：
- D1 真相核查：搜索内容中的可核查声称，返回权威来源
- D5 竞品横评：搜索同主题竞品内容，获取多平台数据指标

合规：AnySearch 是搜索基础设施，只提供公开可检索的 web 内容，
与 TikHub/trafilatura 性质相同——probe 只调接口，原料进结论出由上层负责。
"""
from __future__ import annotations

import os
from typing import Any

import httpx

_API_BASE = "https://api.anysearch.com/v1"
_TIMEOUT = 15


def search(query: str, max_results: int = 5, domain: str | None = None) -> list[dict]:
    """通用搜索，返回结构化结果列表。

    每条结果：{title, url, snippet, content(如有)}
    失败返回空列表（不抛出，降级处理）。
    """
    payload: dict[str, Any] = {"query": query, "max_results": max_results}
    if domain:
        payload["domain"] = domain
    try:
        r = httpx.post(f"{_API_BASE}/search", json=payload,
                       timeout=_TIMEOUT,
                       headers={"Content-Type": "application/json"})
        if r.status_code == 200:
            return r.json().get("data", {}).get("results", [])
    except Exception:
        pass
    return []


def batch_search(queries: list[str], max_results: int = 3) -> list[list[dict]]:
    """批量并行搜索，最多 5 路。返回与 queries 等长的结果列表。"""
    qs = queries[:5]
    payload = {
        "queries": [{"query": q, "max_results": max_results} for q in qs]
    }
    try:
        r = httpx.post(f"{_API_BASE}/batch_search", json=payload,
                       timeout=_TIMEOUT * 2,
                       headers={"Content-Type": "application/json"})
        if r.status_code == 200:
            batched = r.json().get("data", {}).get("results", [])
            return batched if isinstance(batched, list) else [[] for _ in qs]
    except Exception:
        pass
    return [[] for _ in qs]


def extract_url(url: str) -> str:
    """抓取指定 URL 的全文 Markdown（最多 50,000 字符）。失败返回空字符串。"""
    try:
        r = httpx.post(f"{_API_BASE}/extract", json={"url": url},
                       timeout=_TIMEOUT,
                       headers={"Content-Type": "application/json"})
        if r.status_code == 200:
            return r.json().get("data", {}).get("content", "")
    except Exception:
        pass
    return ""
