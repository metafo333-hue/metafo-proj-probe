"""TikTok oEmbed · TikTok 链接元数据（标题/作者/缩略图）· 无需 key · 官方 oEmbed。

端点：
  oembed  GET https://www.tiktok.com/oembed?url={encoded_tiktok_url}
合规：oEmbed 是 TikTok 官方提供的嵌入标准（RFC-compatible），无需注册或 API key，
公开文档 https://developers.tiktok.com/doc/embed-videos/ 明确允许第三方调用。
只返回公开元数据（标题/作者/封面），不含视频内容。失败返回空，不抛出。
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import httpx

META: dict[str, Any] = {
    "id": "tiktok_oembed",
    "domain": ["D6"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["social", "video"],
}

_OEMBED_URL = "https://www.tiktok.com/oembed"
_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}

# TikTok URL 格式校验
_TIKTOK_PATTERN = re.compile(
    r"https?://(www\.)?tiktok\.com/@[\w.]+/video/\d+",
    re.IGNORECASE,
)
# 短链格式
_TIKTOK_SHORT_PATTERN = re.compile(
    r"https?://(vm|vt)\.tiktok\.com/[\w]+",
    re.IGNORECASE,
)


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def get_metadata(url: str) -> dict[str, Any]:
    """取 TikTok 视频的 oEmbed 元数据。

    Args:
        url: TikTok 视频链接，支持：
             - 标准格式: https://www.tiktok.com/@author/video/1234567890
             - 短链格式: https://vm.tiktok.com/XXXXXXXX/

    Returns:
        {"title", "author_name", "author_url", "thumbnail_url", "thumbnail_width",
         "thumbnail_height", "html", "provider_name", "source_id"} 或空 dict。
        html 字段含嵌入代码，上层视需要使用，本层只取元数据。
    """
    if not _is_valid_url(url):
        return {"_error": "not a valid TikTok URL"}
    params = {"url": url}
    try:
        r = httpx.get(_OEMBED_URL, params=params, headers=_HEADERS, timeout=_TIMEOUT,
                      follow_redirects=True)
        if r.status_code != 200:
            return {"_error": f"HTTP {r.status_code}"}
        data = r.json()
        return _normalize(data, url)
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {str(e)[:160]}"}


def batch_metadata(urls: list[str]) -> list[dict[str, Any]]:
    """批量取多个 TikTok 视频元数据（顺序返回，失败条目含 _error 字段）。

    Args:
        urls: TikTok 视频链接列表（最多 20 条）

    Returns:
        与输入 urls 一一对应的结果列表。
    """
    results: list[dict[str, Any]] = []
    for url in urls[:20]:
        results.append(get_metadata(url))
    return results


def _is_valid_url(url: str) -> bool:
    return bool(_TIKTOK_PATTERN.match(url) or _TIKTOK_SHORT_PATTERN.match(url))


def _normalize(data: dict[str, Any], original_url: str) -> dict[str, Any]:
    """标准化 oEmbed 响应（只取元数据，html 嵌入代码保留供上层选用）。"""
    return {
        "title": (data.get("title") or "")[:500],
        "author_name": data.get("author_name", ""),
        "author_url": data.get("author_url", ""),
        "thumbnail_url": data.get("thumbnail_url", ""),
        "thumbnail_width": data.get("thumbnail_width"),
        "thumbnail_height": data.get("thumbnail_height"),
        "provider_name": data.get("provider_name", "TikTok"),
        "type": data.get("type", "video"),
        "version": data.get("version", "1.0"),
        # html 嵌入代码：上层按需使用，本层不主动渲染
        "html": (data.get("html") or "")[:1000],
        "original_url": original_url,
        "source_id": META["id"],
    }
