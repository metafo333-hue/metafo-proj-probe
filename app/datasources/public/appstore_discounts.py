"""App Store 限免 · iTunes 官方 Lookup/Search/RSS API · D15 · 无需 key · 免费。

数据源（实测 2026-06-12 · HTTP 200）：
  fetch_top_free   iTunes RSS https://itunes.apple.com/{country}/rss/topfreeapplications/…/json
                   — 即时榜单（Top Free Apps），原生免费 App
  fetch_search     iTunes Search API https://itunes.apple.com/search?…
                   — 按关键词搜索，price=0 过滤可找免费 App
  lookup_app       iTunes Lookup API https://itunes.apple.com/lookup?id=…
                   — 单 App 元数据（含当前价格），用于判断"原价 → 0 元"是否限免

限免判断策略：
  iTunes API 不直接提供"限免"标签，本模块通过 price==0 + primaryGenreName 推断。
  如需精准历史价格对比，需上层维护价格快照（本模块只返回当前价格，由上层决策）。

合规：iTunes Search/Lookup/RSS API 为 Apple 官方公开接口，无需 key，
      遵守 Apple Service Performance Guidelines（不做实时高频轮询）。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "appstore_discounts",
    "domain": ["D15"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["app_price", "app_discount", "app_free"],
}

_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}

_BASE = "https://itunes.apple.com"


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_top_free(
    country: str = "cn",
    limit: int = 25,
) -> list[dict[str, Any]]:
    """从 iTunes RSS 获取 Top Free App 榜单（原生免费 App）。

    Args:
        country: 国家码，如 "cn" / "us" / "jp"（ISO-2，小写）
        limit:   榜单条数，10 / 25 / 50 / 100

    Returns:
        [{"app_id", "name", "artist", "price", "currency", "genre",
          "icon_url", "store_url", "source_id"}] 或空列表。
    """
    valid_limits = {10, 25, 50, 100}
    limit = min([l for l in valid_limits if l >= limit], default=100)
    url = f"{_BASE}/{country}/rss/topfreeapplications/limit={limit}/json"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        entries = data.get("feed", {}).get("entry", [])
        return [_normalize_rss_entry(e) for e in entries if isinstance(e, dict)]
    except Exception:
        return []


def search_free_apps(
    term: str,
    country: str = "cn",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """用 iTunes Search API 搜索 App，筛选 price=0 的免费 App。

    Args:
        term:    搜索词
        country: 国家码
        limit:   最多返回条数（1-200）

    Returns:
        [{"app_id", "name", "artist", "price", "currency",
          "formatted_price", "genre", "rating", "rating_count",
          "release_date", "description", "icon_url", "store_url",
          "bundle_id", "source_id"}] 或空列表。
    """
    params = {
        "term": term,
        "country": country,
        "media": "software",
        "limit": str(max(1, min(limit, 200))),
    }
    try:
        r = httpx.get(
            f"{_BASE}/search",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])
        return [_normalize_app(a) for a in results if isinstance(a, dict)]
    except Exception:
        return []


def lookup_app(
    app_id: int | str,
    country: str = "cn",
) -> dict[str, Any] | None:
    """通过 App ID 查询单个 App 当前价格与元数据。

    Args:
        app_id:  iTunes App ID（数字），如 364693926（Procreate）
        country: 国家码（不同国家价格可能不同）

    Returns:
        App 信息字典，或 None（App 不存在 / 请求失败）。
        price=0.0 表示当前免费（限免或原生免费）。
    """
    try:
        r = httpx.get(
            f"{_BASE}/lookup",
            params={"id": str(app_id), "country": country},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return None
        results = r.json().get("results", [])
        if not results:
            return None
        return _normalize_app(results[0])
    except Exception:
        return None


def batch_lookup(
    app_ids: list[int | str],
    country: str = "cn",
) -> list[dict[str, Any]]:
    """批量查询多个 App 的当前价格。

    Args:
        app_ids: App ID 列表（最多 100 个，iTunes API 限制）
        country: 国家码

    Returns:
        App 信息列表（顺序与 API 返回一致）。
    """
    ids = app_ids[:100]
    try:
        r = httpx.get(
            f"{_BASE}/lookup",
            params={"id": ",".join(str(i) for i in ids), "country": country},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])
        return [_normalize_app(a) for a in results if isinstance(a, dict)]
    except Exception:
        return []


# ── 内部规范化 ───────────────────────────────────────────────────────────────

def _normalize_app(a: dict[str, Any]) -> dict[str, Any]:
    """标准化 iTunes Search/Lookup API 返回的 App 条目。"""
    return {
        "app_id": a.get("trackId", ""),
        "name": (a.get("trackName") or "")[:200],
        "artist": (a.get("artistName") or "")[:150],
        "price": a.get("price"),
        "currency": a.get("currency", ""),
        "formatted_price": a.get("formattedPrice", ""),
        "genre": a.get("primaryGenreName", ""),
        "genre_id": a.get("primaryGenreId"),
        "rating": a.get("averageUserRating"),
        "rating_count": a.get("userRatingCount"),
        "release_date": (a.get("releaseDate") or "")[:20],
        "description": (a.get("description") or "")[:400],
        "icon_url": a.get("artworkUrl60", ""),
        "store_url": a.get("trackViewUrl", ""),
        "bundle_id": a.get("bundleId", ""),
        "minimum_os_version": a.get("minimumOsVersion", ""),
        "version": a.get("version", ""),
        "file_size_bytes": a.get("fileSizeBytes"),
        "content_advisory_rating": a.get("contentAdvisoryRating", ""),
        "source_id": META["id"],
    }


def _normalize_rss_entry(e: dict[str, Any]) -> dict[str, Any]:
    """标准化 iTunes RSS feed 的 entry 格式。"""
    # RSS entry 使用 im:name / im:price / id / im:artist 等嵌套格式
    name = (e.get("im:name") or {}).get("label", "")
    price_attr = (e.get("im:price") or {})
    price_label = price_attr.get("label", "")
    price_amount = (price_attr.get("attributes") or {}).get("amount", "0")
    currency = (price_attr.get("attributes") or {}).get("currency", "")
    app_id_block = (e.get("id") or {})
    app_id = (app_id_block.get("attributes") or {}).get("im:id", "")
    store_url = app_id_block.get("label", "")
    artist = (e.get("im:artist") or {}).get("label", "")
    genre = (e.get("category") or {}).get("attributes", {}).get("label", "")
    images = e.get("im:image") or []
    icon_url = ""
    if images:
        icon_url = (images[-1] if isinstance(images[-1], dict) else {}).get("label", "")

    try:
        price_float = float(price_amount)
    except (ValueError, TypeError):
        price_float = None

    return {
        "app_id": app_id,
        "name": name[:200],
        "artist": artist[:150],
        "price": price_float,
        "currency": currency,
        "formatted_price": price_label,
        "genre": genre,
        "icon_url": icon_url,
        "store_url": store_url,
        "source_id": META["id"],
    }
