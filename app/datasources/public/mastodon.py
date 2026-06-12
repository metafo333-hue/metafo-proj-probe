"""Mastodon · 联邦社交网络公开时间线与搜索 · 无需 key · 开放联邦 API。

端点（默认实例 mastodon.social，可传入任意实例）：
  timeline   GET https://{instance}/api/v1/timelines/public?local=true&limit=20
  search     GET https://{instance}/api/v2/search?q={query}&type=statuses&limit=20
  account    GET https://{instance}/api/v1/accounts/lookup?acct={username}
  account_statuses GET https://{instance}/api/v1/accounts/{id}/statuses
合规：Mastodon 是 AGPLv3 开源联邦协议，公开时间线 API 无需认证，官方文档明确开放。
失败返回空，不抛出。
注意：搜索 API v2/search 对未认证请求有限制，公开时间线 v1/timelines/public 完全开放。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "mastodon",
    "domain": ["D6"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["social", "search"],
}

_DEFAULT_INSTANCE = "fosstodon.org"   # mastodon.social 已封锁未认证 public timeline（422）
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def public_timeline(
    instance: str = _DEFAULT_INSTANCE,
    limit: int = 20,
    local: bool = True,
    only_media: bool = False,
) -> list[dict[str, Any]]:
    """取实例公开时间线（无需认证）。

    Args:
        instance:    Mastodon 实例域名，如 "mastodon.social" / "fosstodon.org"
        limit:       返回条数（1-40）
        local:       True = 只看本实例嘟文；False = 联邦时间线（跨实例）
        only_media:  True = 只含媒体附件的嘟文

    Returns:
        [{"id", "content_text", "created_at", "url", "account_acct", "account_display_name",
          "replies_count", "reblogs_count", "favourites_count", "tags", "source_id"}]
        或空列表。
    """
    url = f"https://{instance}/api/v1/timelines/public"
    params: dict[str, Any] = {
        "limit": str(max(1, min(limit, 40))),
        "local": "true" if local else "false",
    }
    if only_media:
        params["only_media"] = "true"
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT,
                      follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        return [_normalize_status(s) for s in data]
    except Exception:
        return []


def search(
    query: str,
    instance: str = _DEFAULT_INSTANCE,
    search_type: str = "statuses",
    limit: int = 20,
    resolve: bool = False,
) -> list[dict[str, Any]]:
    """Mastodon 搜索（需实例允许未认证搜索，部分实例限制）。

    Args:
        query:       搜索词（hashtag 加 #，账号加 @）
        instance:    目标实例域名
        search_type: "statuses" / "accounts" / "hashtags"
        limit:       返回条数（1-40）
        resolve:     是否解析远端账号（通常 false）

    Returns:
        statuses 结果的列表，或空列表（实例限制时安静降级）。
    """
    if not query:
        return []
    url = f"https://{instance}/api/v2/search"
    params: dict[str, Any] = {
        "q": query,
        "type": search_type,
        "limit": str(max(1, min(limit, 40))),
        "resolve": "true" if resolve else "false",
    }
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT,
                      follow_redirects=True)
        if r.status_code == 422 or r.status_code == 401:
            # 422 = 缺少认证参数（实例限制）· 安静降级为空
            return []
        if r.status_code != 200:
            return []
        data = r.json()
        results: list[dict[str, Any]] = []
        if search_type == "statuses":
            for s in (data.get("statuses") or []):
                results.append(_normalize_status(s))
        elif search_type == "accounts":
            for acc in (data.get("accounts") or []):
                results.append(_normalize_account(acc))
        elif search_type == "hashtags":
            for tag in (data.get("hashtags") or []):
                results.append({
                    "name": tag.get("name", ""),
                    "url": tag.get("url", ""),
                    "uses": sum(t.get("uses", 0) for t in (tag.get("history") or [])),
                    "source_id": META["id"],
                })
        return results
    except Exception:
        return []


def account_lookup(
    acct: str,
    instance: str = _DEFAULT_INSTANCE,
) -> dict[str, Any]:
    """查询账号信息（支持 user@instance 跨站格式）。

    Args:
        acct:     账号，如 "Mastodon" 或 "user@other.instance"
        instance: 查询的实例（通常用账号所在实例）

    Returns:
        {"id", "acct", "display_name", "followers_count", "following_count",
         "statuses_count", "note_text", "url", "source_id"} 或空 dict。
    """
    url = f"https://{instance}/api/v1/accounts/lookup"
    try:
        r = httpx.get(url, params={"acct": acct}, headers=_HEADERS, timeout=_TIMEOUT,
                      follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        return _normalize_account(data)
    except Exception:
        return {}


def _strip_html(html: str) -> str:
    """极简 HTML 标签去除（不依赖 BeautifulSoup）。"""
    import re
    return re.sub(r"<[^>]+>", "", html or "").strip()[:500]


def _normalize_status(s: dict[str, Any]) -> dict[str, Any]:
    account = s.get("account") or {}
    tags = [t.get("name", "") for t in (s.get("tags") or [])]
    return {
        "id": s.get("id", ""),
        "content_text": _strip_html(s.get("content", "")),
        "created_at": s.get("created_at", ""),
        "url": s.get("url", ""),
        "account_acct": account.get("acct", ""),
        "account_display_name": account.get("display_name", ""),
        "replies_count": s.get("replies_count", 0),
        "reblogs_count": s.get("reblogs_count", 0),
        "favourites_count": s.get("favourites_count", 0),
        "language": s.get("language", ""),
        "tags": tags,
        "media_count": len(s.get("media_attachments") or []),
        "source_id": META["id"],
    }


def _normalize_account(acc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": acc.get("id", ""),
        "acct": acc.get("acct", ""),
        "display_name": acc.get("display_name", ""),
        "followers_count": acc.get("followers_count", 0),
        "following_count": acc.get("following_count", 0),
        "statuses_count": acc.get("statuses_count", 0),
        "note_text": _strip_html(acc.get("note", "")),
        "url": acc.get("url", ""),
        "created_at": acc.get("created_at", ""),
        "bot": acc.get("bot", False),
        "source_id": META["id"],
    }
