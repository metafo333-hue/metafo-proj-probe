"""Hacker News · Algolia Search API · 免费 · 无需 key · 技术舆情 D12。

端点：
  search       GET https://hn.algolia.com/api/v1/search?query=...      — 相关度排序搜索
  search_recent GET https://hn.algolia.com/api/v1/search_by_date?query=...  — 时间倒序搜索
合规：Algolia HN Search API 是 HN 官方授权第三方，公开 API 免费无需注册。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "hackernews",
    "domain": ["D12", "D6"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["news", "search"],
}

_API_BASE = "https://hn.algolia.com/api/v1"
_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search(
    query: str,
    hits_per_page: int = 20,
    tags: str = "story",
    min_points: int = 0,
) -> list[dict[str, Any]]:
    """按关键词搜索 HN 故事（相关度排序）。

    Args:
        query:         关键词，如 "AI agent" / "open source LLM"
        hits_per_page: 返回条数（1-100）
        tags:          Algolia tag 过滤，如 "story"（默认）/ "ask_hn" / "show_hn" / "comment"
        min_points:    最少积分过滤（0 = 不限；建议 10 以过滤噪音）

    Returns:
        [{"id", "title", "url", "author", "points", "num_comments", "created_at",
          "hn_url", "source_id"}] 或空列表。
    """
    params: dict[str, str] = {
        "query": query,
        "hitsPerPage": str(max(1, min(hits_per_page, 100))),
        "tags": tags,
    }
    if min_points > 0:
        params["numericFilters"] = f"points>={min_points}"
    return _fetch(f"{_API_BASE}/search", params)


def search_recent(
    query: str,
    hits_per_page: int = 20,
    tags: str = "story",
) -> list[dict[str, Any]]:
    """按时间倒序搜索最新 HN 故事（近期优先）。

    Args:
        query:         关键词
        hits_per_page: 返回条数（1-100）
        tags:          Algolia tag 过滤

    Returns:
        [{"id", "title", "url", "author", "points", "num_comments", "created_at",
          "hn_url", "source_id"}] 或空列表。
    """
    params: dict[str, str] = {
        "query": query,
        "hitsPerPage": str(max(1, min(hits_per_page, 100))),
        "tags": tags,
    }
    return _fetch(f"{_API_BASE}/search_by_date", params)


def _fetch(url: str, params: dict[str, str]) -> list[dict[str, Any]]:
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        hits = r.json().get("hits") or []
        return [_normalize(h) for h in hits]
    except Exception:
        return []


def _normalize(h: dict[str, Any]) -> dict[str, Any]:
    obj_id = h.get("objectID", "")
    return {
        "id": obj_id,
        "title": (h.get("title") or "")[:300],
        "url": h.get("url", ""),
        "author": h.get("author", ""),
        "points": h.get("points", 0),
        "num_comments": h.get("num_comments", 0),
        "created_at": h.get("created_at", ""),
        "hn_url": f"https://news.ycombinator.com/item?id={obj_id}" if obj_id else "",
        "source_id": META["id"],
    }
