"""YouTube oEmbed · 视频元数据发现 · 免费 · 无需 key · D6。

端点：
  oembed  GET https://www.youtube.com/oembed?url=...&format=json
合规：YouTube oEmbed 是 YouTube 官方公开接口（符合 oEmbed v1 规范），
     无需 API key，返回视频基本元数据（标题/作者/缩略图/尺寸），
     不含受限字段（如精确播放量/评论），官方允许内容聚合与预览用途。
注意：仅返回公开视频；私有/地区限制视频返回 401/404。
🌐 YouTube 在大陆直连可能慢，probe-a 代理验证。
失败返回空，不抛出。
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urlparse, parse_qs

import httpx

META: dict[str, Any] = {
    "id": "youtube_oembed",
    "domain": ["D6"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["video", "social"],
}

_OEMBED_URL = "https://www.youtube.com/oembed"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}

# YouTube URL 匹配正则（支持多种格式）
_YT_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?(?:.*&)?v=|youtu\.be/)([A-Za-z0-9_\-]{11})"),
    re.compile(r"youtube\.com/embed/([A-Za-z0-9_\-]{11})"),
    re.compile(r"youtube\.com/shorts/([A-Za-z0-9_\-]{11})"),
]


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def get_oembed(video_url: str, maxwidth: int = 0, maxheight: int = 0) -> dict[str, Any]:
    """按 YouTube 视频 URL 获取 oEmbed 元数据。

    Args:
        video_url: YouTube 视频 URL，支持：
                   - https://www.youtube.com/watch?v=VIDEO_ID
                   - https://youtu.be/VIDEO_ID
                   - https://www.youtube.com/shorts/VIDEO_ID
        maxwidth:  嵌入播放器最大宽度（像素，0 = 不限）
        maxheight: 嵌入播放器最大高度（像素，0 = 不限）

    Returns:
        {"video_id", "title", "author_name", "author_url", "thumbnail_url",
         "width", "height", "provider_name", "html", "video_url", "source_id"}
        或空 dict（私有视频/地区限制/URL 格式错误）。
    """
    video_id = extract_video_id(video_url)
    # 规范化为标准 watch URL
    canonical_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else video_url
    params: dict[str, str] = {
        "url": canonical_url,
        "format": "json",
    }
    if maxwidth > 0:
        params["maxwidth"] = str(maxwidth)
    if maxheight > 0:
        params["maxheight"] = str(maxheight)
    try:
        r = httpx.get(
            _OEMBED_URL,
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return _normalize(data, video_id or "", canonical_url)
    except Exception:
        return {}


def batch_oembed(
    video_urls: list[str],
    maxwidth: int = 0,
) -> list[dict[str, Any]]:
    """批量查询多个 YouTube 视频 oEmbed 元数据（串行，遇错跳过）。

    Args:
        video_urls: YouTube 视频 URL 列表（最多 50 条，超出截断）
        maxwidth:   最大宽度

    Returns:
        非空结果列表（跳过失败项）。
    """
    results: list[dict[str, Any]] = []
    for url in video_urls[:50]:
        item = get_oembed(url, maxwidth=maxwidth)
        if item:
            results.append(item)
    return results


def extract_video_id(url: str) -> str:
    """从各种 YouTube URL 格式中提取 11 位 video ID。

    Args:
        url: YouTube URL（任意格式）

    Returns:
        11 位 video ID 或空字符串。
    """
    for pattern in _YT_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    # 尝试 query string
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "v" in qs:
            vid = qs["v"][0]
            if len(vid) == 11:
                return vid
    except Exception:
        pass
    return ""


def video_url_from_id(video_id: str) -> str:
    """从 video ID 构造标准 YouTube URL。"""
    return f"https://www.youtube.com/watch?v={video_id}"


def _normalize(data: dict[str, Any], video_id: str, video_url: str) -> dict[str, Any]:
    return {
        "video_id": video_id,
        "title": (data.get("title") or "")[:500],
        "author_name": (data.get("author_name") or "")[:200],
        "author_url": data.get("author_url", ""),
        "thumbnail_url": data.get("thumbnail_url", ""),
        "thumbnail_width": data.get("thumbnail_width", 0),
        "thumbnail_height": data.get("thumbnail_height", 0),
        "width": data.get("width", 0),
        "height": data.get("height", 0),
        "provider_name": data.get("provider_name", "YouTube"),
        "provider_url": data.get("provider_url", "https://www.youtube.com/"),
        "html": (data.get("html") or "")[:1000],
        "video_url": video_url,
        "source_id": META["id"],
    }
