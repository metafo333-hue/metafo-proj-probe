"""GDELT Doc API v2 · 无需 key · 免费 · 公开数据集。

端点：
  search  https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=ArtList&...
合规：GDELT Project 官方开放 API，无 ToS 限制，公共开放数据。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "gdelt",
    "domain": ["D1", "D9", "D6"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["news", "search"],
}

_API_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def search(
    query: str,
    max_records: int = 20,
    timespan: str = "1week",
    sourcelang: str = "",
) -> list[dict[str, Any]]:
    """全球新闻全文检索（GDELT Doc API）。

    Args:
        query:       搜索词（支持布尔运算 AND/OR/NOT）
        max_records: 返回条数，1-250
        timespan:    时间范围，如 "1week" / "1month" / "1day"
        sourcelang:  限定语言，如 "chinese" / "english"，空字符串表示不限

    Returns:
        列表，每条包含 {title, url, domain, date, language, source_id}。
        失败返回空列表。
    """
    max_records = min(max(1, max_records), 250)
    params: dict[str, str] = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": str(max_records),
        "timespan": timespan,
        "format": "json",
    }
    if sourcelang:
        params["sourcelang"] = sourcelang
    try:
        r = httpx.get(_API_BASE, params=params, timeout=_TIMEOUT, headers=_HEADERS)
        if r.status_code != 200:
            return []
        data = r.json()
        articles = data.get("articles") or []
        results: list[dict[str, Any]] = []
        for art in articles:
            results.append({
                "title": (art.get("title") or "").strip()[:500],
                "url": art.get("url", ""),
                "domain": art.get("domain", ""),
                "date": art.get("seendate", ""),
                "language": art.get("language", ""),
                "source_country": art.get("sourcecountry", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []
