"""Wayback Machine · Internet Archive · 无需 key · 免费 · 公有领域。

端点：
  availability  https://archive.org/wayback/available?url=...&timestamp=...
  cdx_search    http://web.archive.org/cdx/search/cdx?url=...&output=json&...
合规：Internet Archive 公共 API，官方文档明确允许第三方调用。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "webarchive",
    "domain": ["D4", "D1"],
    "access_type": "free",
    "kinds": ["archive", "availability"],
}

_AVAIL_API = "https://archive.org/wayback/available"
_CDX_API = "http://web.archive.org/cdx/search/cdx"
_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def availability(url: str, timestamp: str = "") -> dict[str, Any]:
    """检查某 URL 是否有存档，返回最近快照信息。

    Args:
        url:       目标 URL
        timestamp: 可选，YYYYMMDDHHMMSS 格式

    返回 {available, url, timestamp, status} 或空 dict。
    """
    params: dict[str, str] = {"url": url}
    if timestamp:
        params["timestamp"] = timestamp
    try:
        r = httpx.get(_AVAIL_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code == 200:
            d = r.json()
            snap = d.get("archived_snapshots", {}).get("closest", {})
            if snap:
                return {
                    "available": snap.get("available", False),
                    "url": snap.get("url", ""),
                    "timestamp": snap.get("timestamp", ""),
                    "status": snap.get("status", ""),
                    "original_url": url,
                    "source_id": META["id"],
                }
            return {"available": False, "original_url": url, "source_id": META["id"]}
    except Exception:
        pass
    return {}


def cdx_search(
    url: str,
    limit: int = 5,
    from_year: str = "",
    to_year: str = "",
) -> list[dict[str, Any]]:
    """CDX API 查询历史快照列表。每条：{timestamp, original, statuscode, mimetype}。

    Args:
        url:       目标 URL（支持通配符，如 "example.com/*"）
        limit:     最多返回条数
        from_year: 起始年份 YYYY（可选）
        to_year:   截止年份 YYYY（可选）
    """
    params: dict[str, str] = {
        "url": url,
        "output": "json",
        "limit": str(min(limit, 20)),
        "fl": "timestamp,original,statuscode,mimetype",
        "collapse": "timestamp:6",   # 按月去重
    }
    if from_year:
        params["from"] = from_year
    if to_year:
        params["to"] = to_year
    try:
        r = httpx.get(_CDX_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code == 200:
            rows = r.json()
            if not isinstance(rows, list) or len(rows) < 2:
                return []
            headers_row = rows[0]
            results = []
            for row in rows[1:]:
                entry = dict(zip(headers_row, row))
                entry["source_id"] = META["id"]
                results.append(entry)
            return results
    except Exception:
        pass
    return []
