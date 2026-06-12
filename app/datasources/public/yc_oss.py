"""YC OSS · Y Combinator 公司数据库（开源版）· 无需 key · 免费。

端点：
  all_companies  GET https://yc-oss.github.io/api/companies/all.json
合规：yc-oss 是 GitHub Pages 托管的 YC 数据镜像，采用 MIT License，
数据来源于 YC 官方公开目录，允许任何用途使用。
失败返回空，不抛出。注意：文件较大（~1MB），会缓存到模块内存中避免重复下载。

批次格式说明：实际批次名为 "Winter 2024" / "Summer 2023"（全称），
  可传入全称或 W/S 缩写（"W24" 会自动转为 "Winter 2024"）。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "yc_oss",
    "domain": ["D17", "D11"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["company", "startup"],
}

_BASE_URL = "https://yc-oss.github.io/api"
_ALL_URL = f"{_BASE_URL}/companies/all.json"
_TIMEOUT = 30  # 大文件需要更长超时
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}

# 模块级缓存（生命周期内一次下载）
_cache: list[dict[str, Any]] | None = None

# 批次缩写映射
_SEASON_MAP = {"W": "Winter", "S": "Summer"}


def _normalize_batch(batch: str) -> str:
    """将批次缩写转为全称：'W24' → 'Winter 2024'，'S23' → 'Summer 2023'。
    已是全称（如 'Winter 2024'）直接返回。
    """
    if not batch:
        return ""
    # 已是全称
    if batch.startswith("Winter") or batch.startswith("Summer"):
        return batch
    # 缩写格式 W24 / S23
    if len(batch) >= 3 and batch[0].upper() in _SEASON_MAP:
        season = _SEASON_MAP[batch[0].upper()]
        year_part = batch[1:].strip()
        if year_part.isdigit():
            year = int(year_part)
            full_year = 2000 + year if year < 100 else year
            return f"{season} {full_year}"
    return batch


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def all_companies(force_reload: bool = False) -> list[dict[str, Any]]:
    """取全量 YC 公司列表（~5000 家，含历史批次）。

    Args:
        force_reload: True = 强制重新下载（忽略缓存）

    Returns:
        完整 YC 公司列表，每条含 {"id", "name", "batch", "status", "tags",
        "description", "url", "source_id"} 等字段。失败返回空列表。
    """
    global _cache
    if _cache is not None and not force_reload:
        return _cache
    try:
        r = httpx.get(_ALL_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        _cache = [_normalize(c) for c in data]
        return _cache
    except Exception:
        return []


def search(
    keyword: str = "",
    batch: str = "",
    status: str = "",
    tag: str = "",
    top_n: int = 50,
) -> list[dict[str, Any]]:
    """搜索过滤 YC 公司（本地过滤，依赖 all_companies 缓存）。

    Args:
        keyword: 公司名 / 描述关键词（大小写不敏感）
        batch:   批次，如 "W24" / "S23" / "W21"（精确匹配）
        status:  "Active" / "Inactive" / "Acquired" / "Public"（精确匹配）
        tag:     标签，如 "B2B" / "AI" / "Fintech"（含匹配）
        top_n:   最多返回条数（1-500）

    Returns:
        过滤后的公司列表（不超过 top_n 条）。
    """
    companies = all_companies()
    if not companies:
        return []

    results: list[dict[str, Any]] = []
    kw_lower = keyword.lower() if keyword else ""
    batch_normalized = _normalize_batch(batch) if batch else ""

    for c in companies:
        if batch_normalized and c.get("batch", "") != batch_normalized:
            continue
        if status and c.get("status", "") != status:
            continue
        if tag:
            tags_lower = [t.lower() for t in (c.get("tags") or [])]
            if tag.lower() not in tags_lower:
                continue
        if kw_lower:
            name_hit = kw_lower in c.get("name", "").lower()
            desc_hit = kw_lower in c.get("description", "").lower()
            if not (name_hit or desc_hit):
                continue
        results.append(c)
        if len(results) >= max(1, min(top_n, 500)):
            break

    return results


def by_batch(batch: str) -> list[dict[str, Any]]:
    """取指定批次的 YC 公司（如 "W24" / "S23"）。

    Args:
        batch: YC 批次，格式 "{W/S}{YY}"，如 "W24" / "S23"

    Returns:
        该批次的公司列表，或空列表。优先从全量缓存过滤，避免重复请求。
    """
    batch_normalized = _normalize_batch(batch)
    # 先尝试从缓存过滤
    if _cache is not None:
        return [c for c in _cache if c.get("batch") == batch_normalized]
    # 缓存空则尝试从全量下载后过滤
    url = f"{_BASE_URL}/batches/{batch.lower()}.json"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            # 降级到全量过滤
            return search(batch=batch_normalized)
        data = r.json()
        if not isinstance(data, list):
            return []
        return [_normalize(c) for c in data]
    except Exception:
        return search(batch=batch)


def _normalize(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": c.get("id", ""),
        "name": c.get("name", ""),
        "slug": c.get("slug", ""),
        "batch": c.get("batch", ""),
        "status": c.get("status", ""),
        "description": (c.get("long_description") or c.get("one_liner") or "")[:300],
        "one_liner": (c.get("one_liner") or "")[:200],
        "tags": c.get("tags") or [],
        "industries": c.get("industries") or [],
        "url": c.get("website") or c.get("url", ""),
        "ycdc_url": f"https://www.ycombinator.com/companies/{c.get('slug', '')}",
        "team_size": c.get("team_size"),
        "country": c.get("country", ""),
        "source_id": META["id"],
    }
