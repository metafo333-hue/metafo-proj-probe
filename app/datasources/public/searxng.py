"""SearXNG · 自托管搜索聚合 · 读 PROBE_SEARXNG_BASE env · 免费 · AGPL-3.0。

未配置 PROBE_SEARXNG_BASE → 立即返回空（不报错）。
端点：GET {base}/search?q=...&format=json&...
合规：调用自托管实例，不违反任何第三方平台 ToS。
失败返回空，不抛出。
"""
from __future__ import annotations

import os
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "searxng",
    "domain": ["D1", "D5", "D7"],
    "access_type": "free",
    "kinds": ["search"],
}

_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def _base() -> str:
    """返回 SearXNG base URL，未配置则返回空字符串。"""
    return os.getenv("PROBE_SEARXNG_BASE", "").rstrip("/")


def search(
    query: str,
    categories: list[str] | None = None,
    engines: list[str] | None = None,
    language: str = "auto",
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """全文搜索。未配置 PROBE_SEARXNG_BASE 时立即返回空列表。

    Args:
        query:       搜索词
        categories:  如 ["general", "news"] (SearXNG 分类)
        engines:     指定引擎，如 ["google", "bing"]（可选）
        language:    语言代码，如 "zh-CN"
        max_results: 最多返回条数（取前 N 条）

    每条结果：{title, url, content, engine, score}
    """
    base = _base()
    if not base:
        return []
    params: dict[str, str] = {
        "q": query,
        "format": "json",
        "language": language,
    }
    if categories:
        params["categories"] = ",".join(categories)
    if engines:
        params["engines"] = ",".join(engines)
    try:
        r = httpx.get(
            f"{base}/search",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            results = r.json().get("results", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": (item.get("content") or "")[:400],
                    "engine": item.get("engine", ""),
                    "score": item.get("score", 0),
                    "source_id": META["id"],
                }
                for item in results[:max_results]
            ]
    except Exception:
        pass
    return []


def configured() -> bool:
    """返回 SearXNG 是否已配置（仅检查 env，不发请求）。"""
    return bool(_base())
