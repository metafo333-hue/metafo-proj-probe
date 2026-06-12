"""arXiv API · 无需 key · 免费 · arXiv 许可证（作者版权）。

端点：
  search  http://export.arxiv.org/api/query?search_query=...&max_results=...
合规：官方 Atom/XML API，arXiv ToS 明确允许程序化批量调用，须合理限速。
失败返回空，不抛出。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "arxiv",
    "domain": ["D10", "D5"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["paper", "search"],
}

_API_BASE = "http://export.arxiv.org/api/query"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/atom+xml",
}

# Atom 命名空间
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """按关键词检索 arXiv 论文。

    Args:
        query:       检索词，支持 arXiv 查询语法（如 "ti:transformer"）
        max_results: 返回条数，最大 100

    Returns:
        列表，每条包含 {id, title, summary, authors, published, url, source_id}。
        失败返回空列表。
    """
    max_results = min(max(1, max_results), 100)
    params = {
        "search_query": f"all:{query}",
        "start": "0",
        "max_results": str(max_results),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    try:
        r = httpx.get(_API_BASE, params=params, timeout=_TIMEOUT, headers=_HEADERS)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.text)
        results: list[dict[str, Any]] = []
        for entry in root.findall("atom:entry", _NS):
            arxiv_id = (entry.findtext("atom:id", default="", namespaces=_NS) or "").strip()
            title = (entry.findtext("atom:title", default="", namespaces=_NS) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=_NS) or "").strip()[:1000]
            published = (entry.findtext("atom:published", default="", namespaces=_NS) or "").strip()
            authors = [
                (a.findtext("atom:name", default="", namespaces=_NS) or "").strip()
                for a in entry.findall("atom:author", _NS)
            ]
            # 规范 URL：取 /abs/ 链接
            url = ""
            for link in entry.findall("atom:link", _NS):
                if link.get("type") == "text/html":
                    url = link.get("href", "")
                    break
            if not url and arxiv_id:
                url = arxiv_id  # arxiv_id 本身即为 https://arxiv.org/abs/... 链接
            results.append({
                "id": arxiv_id,
                "title": title,
                "summary": summary,
                "authors": authors[:5],  # 最多 5 位
                "published": published[:10],  # YYYY-MM-DD
                "url": url,
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []
