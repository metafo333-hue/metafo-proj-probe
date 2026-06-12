"""OpenAlex · 学术论文开放数据库 · Our Research · 无需 key · 免费 · CC0。

端点：
  search_works  GET https://api.openalex.org/works?search=...  — 全文搜索论文
  get_work      GET https://api.openalex.org/works/{id}         — 按 OpenAlex/DOI id 取详情
合规：OpenAlex 是 Our Research 维护的开放学术图谱，CC0 公有领域，无速率限制（polite pool 建议
带邮箱 User-Agent）。替代/补充 D5 竞品分析 + D10 学术基础。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "openalex",
    "domain": ["D10", "D5"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["paper", "search"],
}

_API_BASE = "https://api.openalex.org"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search_works(
    query: str,
    per_page: int = 20,
    sort: str = "relevance_score:desc",
    from_year: int = 0,
) -> list[dict[str, Any]]:
    """全文搜索学术论文。

    Args:
        query:     关键词，如 "large language model" / "RAG retrieval"
        per_page:  返回条数（1-50）
        sort:      排序方式，如 "relevance_score:desc" / "publication_year:desc" / "cited_by_count:desc"
        from_year: 仅返回该年份及之后的论文（0 = 不限）

    Returns:
        [{"id", "doi", "title", "authors", "venue", "year", "cited_by_count",
          "open_access", "abstract_url", "source_id"}] 或空列表。
    """
    params: dict[str, str] = {
        "search": query,
        "per_page": str(max(1, min(per_page, 50))),
        "sort": sort,
        "select": "id,doi,title,display_name,authorships,publication_year,cited_by_count,open_access,primary_location,abstract_inverted_index",
    }
    if from_year:
        params["filter"] = f"publication_year:>{from_year - 1}"
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
        results = data.get("results") or []
        return [_normalize_work(w) for w in results]
    except Exception:
        return []


def get_work(work_id: str) -> dict[str, Any]:
    """按 OpenAlex id（如 "W2741809807"）或 DOI（如 "10.1234/xxx"）取论文详情。

    Args:
        work_id: OpenAlex Work ID（以 W 开头）或完整 DOI 字符串

    Returns:
        标准化论文详情 dict，失败返回空 dict。
    """
    # 若传入 DOI，转换为 OpenAlex DOI filter
    if work_id.startswith("10."):
        endpoint = f"{_API_BASE}/works/doi:{work_id}"
    elif work_id.startswith("https://doi.org/"):
        endpoint = f"{_API_BASE}/works/doi:{work_id.replace('https://doi.org/', '')}"
    else:
        endpoint = f"{_API_BASE}/works/{work_id}"
    try:
        r = httpx.get(endpoint, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code == 200:
            return _normalize_work(r.json())
    except Exception:
        pass
    return {}


def _normalize_work(w: dict[str, Any]) -> dict[str, Any]:
    """标准化论文元数据。"""
    # 作者列表（取前5位）
    authorships = w.get("authorships") or []
    authors = [
        a.get("author", {}).get("display_name", "")
        for a in authorships[:5]
        if isinstance(a, dict)
    ]
    # 期刊/来源
    primary_loc = w.get("primary_location") or {}
    source = primary_loc.get("source") or {}
    venue = source.get("display_name", "")
    # open access
    oa = w.get("open_access") or {}
    return {
        "id": (w.get("id") or "").replace("https://openalex.org/", ""),
        "doi": w.get("doi", ""),
        "title": (w.get("display_name") or w.get("title") or "")[:300],
        "authors": authors,
        "venue": venue[:150],
        "year": w.get("publication_year"),
        "cited_by_count": w.get("cited_by_count", 0),
        "open_access": oa.get("is_oa", False),
        "oa_url": oa.get("oa_url", ""),
        "source_id": META["id"],
    }
