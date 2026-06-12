"""iTunes Search / Lookup API · 播客、App、音乐发现 · 免费 · 无需 key · D6。

端点：
  search  GET https://itunes.apple.com/search?term=...&media=...
  lookup  GET https://itunes.apple.com/lookup?id=...
合规：Apple iTunes Search API，官方公开端点，无需注册，允许第三方发现/聚合用途。
     请求频率建议 ≤20 次/分钟（官方建议）。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "itunes_search",
    "domain": ["D6"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["podcast", "app", "music", "ebook"],
}

_API_BASE = "https://itunes.apple.com"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}

# 支持的媒体类型
MEDIA_TYPES = (
    "podcast",
    "music",
    "musicVideo",
    "audiobook",
    "shortFilm",
    "tvShow",
    "movie",
    "ebook",
    "software",
    "all",
)


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search(
    term: str,
    media: str = "podcast",
    limit: int = 20,
    country: str = "US",
    lang: str = "en_us",
    explicit: str = "Yes",
) -> list[dict[str, Any]]:
    """按关键词搜索 iTunes / App Store / Podcast 内容。

    Args:
        term:     搜索词，如 "machine learning" / "tech news"
        media:    媒体类型，"podcast"（默认）/ "music" / "software" / "ebook" / "all"
        limit:    返回条数（1-200）
        country:  国家/地区码，如 "US" / "CN" / "JP"
        lang:     返回语言，如 "en_us" / "zh_cn"
        explicit: 是否包含限制级内容，"Yes" / "No"

    Returns:
        [{"collection_id", "collection_name", "artist_name", "kind",
          "artwork_url", "feed_url", "genre", "track_count",
          "release_date", "description", "source_id"}]
        或空列表。
    """
    params: dict[str, str] = {
        "term": term,
        "media": media if media in MEDIA_TYPES else "podcast",
        "limit": str(min(max(1, limit), 200)),
        "country": country,
        "lang": lang,
        "explicit": explicit,
    }
    try:
        r = httpx.get(
            f"{_API_BASE}/search",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        results_raw = data.get("results") or []
        return [_normalize(item) for item in results_raw]
    except Exception:
        return []


def lookup(
    itunes_id: int | str,
    entity: str = "podcast",
) -> dict[str, Any]:
    """按 iTunes ID 精确查询单条内容元数据。

    Args:
        itunes_id: iTunes 集合 ID 或曲目 ID（数字或字符串）
        entity:    关联实体类型，如 "podcast" / "album" / "song"

    Returns:
        单条内容 dict 或空 dict。
    """
    params: dict[str, str] = {
        "id": str(itunes_id),
        "entity": entity,
    }
    try:
        r = httpx.get(
            f"{_API_BASE}/lookup",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        results_raw = data.get("results") or []
        return _normalize(results_raw[0]) if results_raw else {}
    except Exception:
        return {}


def lookup_podcast_episodes(
    podcast_id: int | str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """查询播客的最新单集列表。

    Args:
        podcast_id: 播客的 iTunes Collection ID
        limit:      返回单集数量（1-200）

    Returns:
        [{"track_id", "track_name", "description", "release_date",
          "duration_ms", "content_url", "source_id"}]
        或空列表。
    """
    params: dict[str, str] = {
        "id": str(podcast_id),
        "entity": "podcastEpisode",
        "limit": str(min(max(1, limit), 200)),
    }
    try:
        r = httpx.get(
            f"{_API_BASE}/lookup",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        results_raw = data.get("results") or []
        # 第一条是播客本身，跳过；后续为单集
        episodes = [item for item in results_raw if item.get("wrapperType") == "podcastEpisode"]
        return [_normalize_episode(ep) for ep in episodes]
    except Exception:
        return []


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    kind = item.get("kind") or item.get("wrapperType", "")
    return {
        "collection_id": item.get("collectionId") or item.get("trackId"),
        "track_id": item.get("trackId"),
        "collection_name": (item.get("collectionName") or "")[:300],
        "track_name": (item.get("trackName") or "")[:300],
        "artist_name": (item.get("artistName") or "")[:200],
        "kind": kind,
        "artwork_url": item.get("artworkUrl600") or item.get("artworkUrl100", ""),
        "feed_url": item.get("feedUrl", ""),
        "genre": item.get("primaryGenreName", ""),
        "genres": item.get("genres") or [],
        "track_count": item.get("trackCount", 0),
        "release_date": item.get("releaseDate", ""),
        "description": (item.get("description") or item.get("longDescription") or "")[:1000],
        "country": item.get("country", ""),
        "content_advisory": item.get("contentAdvisoryRating", ""),
        "source_id": META["id"],
    }


def _normalize_episode(ep: dict[str, Any]) -> dict[str, Any]:
    return {
        "track_id": ep.get("trackId"),
        "track_name": (ep.get("trackName") or "")[:300],
        "description": (ep.get("description") or "")[:1000],
        "release_date": ep.get("releaseDate", ""),
        "duration_ms": ep.get("trackTimeMillis", 0),
        "episode_url": ep.get("episodeUrl", ""),
        "content_url": ep.get("episodeUrl", ""),
        "episode_guid": ep.get("episodeGuid", ""),
        "collection_id": ep.get("collectionId"),
        "source_id": META["id"],
    }
