"""Wikipedia / Wikimedia REST API · 无需 key · 免费 · CC BY-SA 4.0。

端点：
  summary  https://en.wikipedia.org/api/rest_v1/page/summary/{title}
  search   https://en.wikipedia.org/w/api.php?action=opensearch&...
合规：官方 REST API，Wikimedia ToS 明确允许第三方批量调用，须带合理 User-Agent。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "wikipedia",
    "domain": ["D1", "D4", "D10"],
    "access_type": "free",
    "kinds": ["article", "search"],
}

_API_BASE = "https://en.wikipedia.org/api/rest_v1"
_SEARCH_API = "https://en.wikipedia.org/w/api.php"
_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def summary(title: str, lang: str = "en") -> dict[str, Any]:
    """取指定词条摘要。返回 {title, extract, url, pageid} 或空 dict。

    Args:
        title: 词条名（空格用下划线或空格均可）
        lang:  语言代码，默认 "en"，中文用 "zh"
    """
    base = f"https://{lang}.wikipedia.org/api/rest_v1"
    encoded = httpx.URL("").copy_with(path=title).path.lstrip("/")
    try:
        r = httpx.get(
            f"{base}/page/summary/{httpx.URL(title)}",
            timeout=_TIMEOUT,
            headers=_HEADERS,
            follow_redirects=True,
        )
        if r.status_code == 200:
            d = r.json()
            return {
                "title": d.get("title", ""),
                "extract": d.get("extract", "")[:2000],
                "url": d.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "pageid": d.get("pageid"),
                "lang": lang,
                "source_id": META["id"],
            }
    except Exception:
        pass
    return {}


def search(query: str, limit: int = 5, lang: str = "en") -> list[dict[str, Any]]:
    """OpenSearch 全文检索，返回结果列表。

    每条：{title, url, snippet}
    失败返回空列表。
    """
    params = {
        "action": "opensearch",
        "search": query,
        "limit": str(min(limit, 10)),
        "namespace": "0",
        "format": "json",
    }
    try:
        base_search = f"https://{lang}.wikipedia.org/w/api.php"
        r = httpx.get(base_search, params=params, timeout=_TIMEOUT, headers=_HEADERS)
        if r.status_code == 200:
            data = r.json()
            # OpenSearch 返回 [query, [titles], [snippets], [urls]]
            if isinstance(data, list) and len(data) == 4:
                titles = data[1] or []
                snippets = data[2] or []
                urls = data[3] or []
                return [
                    {"title": t, "snippet": s[:300], "url": u, "source_id": META["id"]}
                    for t, s, u in zip(titles, snippets, urls)
                ]
    except Exception:
        pass
    return []
