"""Crossref · 学术文献元数据 API · 免费 · 无需 key（polite pool 加 mailto）· D10。

端点：
  search   GET https://api.crossref.org/works?query=...&mailto=...
  get_doi  GET https://api.crossref.org/works/{doi}
合规：Crossref REST API，公开免费端点，带 mailto 参数进入 polite pool（更高速率限制）。
     数据为书目元数据，Crossref ToS 允许非商业研究与分析使用。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

META: dict[str, Any] = {
    "id": "crossref",
    "domain": ["D10"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["paper", "doi", "citation"],
}

_API_BASE = "https://api.crossref.org"
_POLITE_MAILTO = "probe@metafoclaw.com"  # polite pool，提高速率
_TIMEOUT = 25
_HEADERS = {
    "User-Agent": f"probe-intel/1.0 (metafoclaw.com; mailto:{_POLITE_MAILTO})",
    "Accept": "application/json",
}

# 支持的文献类型
WORK_TYPES = (
    "journal-article",
    "book-chapter",
    "proceedings-article",
    "book",
    "report",
    "preprint",
    "posted-content",
    "dataset",
)


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search(
    query: str,
    rows: int = 20,
    offset: int = 0,
    work_type: str = "",
    from_pub_date: str = "",
    until_pub_date: str = "",
    sort: str = "relevance",
) -> list[dict[str, Any]]:
    """按关键词搜索学术文献元数据。

    Args:
        query:          搜索词（标题、摘要、作者等全文检索）
        rows:           返回条数（1-1000，建议 ≤100）
        offset:         分页偏移
        work_type:      文献类型过滤，如 "journal-article" / "preprint" / "book"
        from_pub_date:  发表日期起，格式 "YYYY-MM-DD" 或 "YYYY"
        until_pub_date: 发表日期止，格式同上
        sort:           排序方式，"relevance"（默认）/ "published" / "indexed"

    Returns:
        [{"doi", "title", "authors", "published_date", "type", "is_oa",
          "container_title", "publisher", "references_count",
          "citations_count", "abstract", "url", "source_id"}]
        或空列表。
    """
    params: dict[str, str] = {
        "query": query,
        "rows": str(min(max(1, rows), 1000)),
        "offset": str(max(0, offset)),
        "sort": sort,
        "mailto": _POLITE_MAILTO,
    }
    if work_type:
        params["filter"] = _build_filter(work_type, from_pub_date, until_pub_date)
    elif from_pub_date or until_pub_date:
        params["filter"] = _build_filter("", from_pub_date, until_pub_date)
    try:
        r = httpx.get(
            f"{_API_BASE}/works",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        msg = data.get("message") or {}
        items = msg.get("items") or []
        return [_normalize(item) for item in items]
    except Exception:
        return []


def get_doi(doi: str) -> dict[str, Any]:
    """按 DOI 精确查询文献元数据。

    Args:
        doi: 文献 DOI，如 "10.1038/s41586-024-07487-w"

    Returns:
        单条文献 dict 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_API_BASE}/works/{quote(doi, safe='')}",
            params={"mailto": _POLITE_MAILTO},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        msg = data.get("message") or {}
        if not isinstance(msg, dict):
            return {}
        return _normalize(msg)
    except Exception:
        return {}


def search_by_author(
    author_name: str,
    rows: int = 20,
) -> list[dict[str, Any]]:
    """按作者名搜索文献（使用 query.author 字段）。

    Args:
        author_name: 作者姓名，如 "Yann LeCun" / "Yoshua Bengio"
        rows:        返回条数

    Returns:
        [{"doi", "title", "authors", "published_date", ...}] 或空列表。
    """
    params: dict[str, str] = {
        "query.author": author_name,
        "rows": str(min(max(1, rows), 200)),
        "mailto": _POLITE_MAILTO,
    }
    try:
        r = httpx.get(
            f"{_API_BASE}/works",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = (data.get("message") or {}).get("items") or []
        return [_normalize(item) for item in items]
    except Exception:
        return []


def _build_filter(work_type: str, from_date: str, until_date: str) -> str:
    parts = []
    if work_type:
        parts.append(f"type:{work_type}")
    if from_date:
        parts.append(f"from-pub-date:{from_date}")
    if until_date:
        parts.append(f"until-pub-date:{until_date}")
    return ",".join(parts)


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    # 标题
    titles = item.get("title") or []
    title = titles[0][:500] if titles else ""
    # 容器标题（期刊/会议名）
    container_titles = item.get("container-title") or []
    container_title = container_titles[0][:300] if container_titles else ""
    # 作者列表
    authors_raw = item.get("author") or []
    authors = []
    for a in authors_raw[:10]:
        given = a.get("given", "")
        family = a.get("family", "")
        name = f"{given} {family}".strip() if (given or family) else a.get("name", "")
        if name:
            authors.append(name[:100])
    # 发布日期
    published = item.get("published") or item.get("published-print") or item.get("published-online") or {}
    date_parts = (published.get("date-parts") or [[]])[0]
    if date_parts:
        published_date = "-".join(str(p).zfill(2) for p in date_parts)
    else:
        published_date = ""
    # 开放获取
    oa_status = item.get("is-referenced-by-count")
    return {
        "doi": item.get("DOI", ""),
        "title": title,
        "authors": authors,
        "published_date": published_date,
        "type": item.get("type", ""),
        "container_title": container_title,
        "publisher": (item.get("publisher") or "")[:200],
        "abstract": (item.get("abstract") or "")[:1000],
        "references_count": item.get("references-count", 0),
        "citations_count": oa_status or 0,
        "url": item.get("URL", ""),
        "subject": item.get("subject") or [],
        "source_id": META["id"],
    }
