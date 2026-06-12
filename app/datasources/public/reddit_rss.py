"""Reddit 公开 JSON/RSS · 子版块热帖与搜索 · 免费 · 无需 key · D6。

端点（官方公开端点）：
  hot_posts   GET https://www.reddit.com/r/{subreddit}/hot.json
  new_posts   GET https://www.reddit.com/r/{subreddit}/new.json
  search      GET https://www.reddit.com/search.json?q=...
合规：Reddit 公开 API 端点（.json 后缀），官方允许非登录访问。
     必须带规范 User-Agent（否则 403）：格式 "platform:appid:version (by /u/username)"。
     不使用 OAuth / 不访问需授权端点 / 不模拟登录。
失败返回空（含 403 / 429 限流），不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "reddit_rss",
    "domain": ["D6"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["social", "forum", "news"],
}

_API_BASE = "https://www.reddit.com"
_TIMEOUT = 20
# Reddit 要求规范 User-Agent，否则 403
_HEADERS = {
    "User-Agent": "probe-intel:v1.0 (by /u/probe_meta)",
    "Accept": "application/json",
}

# 常用技术/科技子版块
DEFAULT_SUBREDDITS = (
    "programming",
    "technology",
    "MachineLearning",
    "artificial",
    "dataisbeautiful",
    "opensource",
)


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def hot_posts(
    subreddit: str = "programming",
    limit: int = 25,
    after: str = "",
) -> list[dict[str, Any]]:
    """获取子版块热帖列表。

    Args:
        subreddit: 子版块名，如 "programming" / "MachineLearning" / "technology"
        limit:     返回条数（1-100）
        after:     分页游标（上次结果的 `after` 字段）

    Returns:
        [{"id", "title", "author", "subreddit", "score", "num_comments",
          "url", "selftext", "created_utc", "permalink", "source_id"}]
        或空列表（含 403/限流情况）。
    """
    params: dict[str, str] = {"limit": str(min(max(1, limit), 100))}
    if after:
        params["after"] = after
    return _fetch_listing(f"{_API_BASE}/r/{subreddit}/hot.json", params)


def new_posts(
    subreddit: str = "programming",
    limit: int = 25,
    after: str = "",
) -> list[dict[str, Any]]:
    """获取子版块最新帖子。

    Args:
        subreddit: 子版块名
        limit:     返回条数（1-100）
        after:     分页游标

    Returns:
        [{"id", "title", "author", ...}] 或空列表。
    """
    params: dict[str, str] = {"limit": str(min(max(1, limit), 100))}
    if after:
        params["after"] = after
    return _fetch_listing(f"{_API_BASE}/r/{subreddit}/new.json", params)


def search(
    query: str,
    subreddit: str = "",
    limit: int = 25,
    sort: str = "relevance",
    time_filter: str = "all",
) -> list[dict[str, Any]]:
    """全站或子版块内搜索帖子。

    Args:
        query:       搜索词
        subreddit:   限定子版块（空字符串 = 全站搜索）
        limit:       返回条数（1-100）
        sort:        排序方式，"relevance"（默认）/ "hot" / "new" / "top"
        time_filter: 时间过滤，"all"（默认）/ "day" / "week" / "month" / "year"

    Returns:
        [{"id", "title", "author", ...}] 或空列表。
    """
    params: dict[str, str] = {
        "q": query,
        "limit": str(min(max(1, limit), 100)),
        "sort": sort,
        "t": time_filter,
        "type": "link",
    }
    if subreddit:
        url = f"{_API_BASE}/r/{subreddit}/search.json"
        params["restrict_sr"] = "1"
    else:
        url = f"{_API_BASE}/search.json"
    return _fetch_listing(url, params)


def _fetch_listing(url: str, params: dict[str, str]) -> list[dict[str, Any]]:
    try:
        r = httpx.get(
            url,
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            # 403 = 需要授权或被封 IP，429 = 限流，返回空不抛错
            return []
        data = r.json()
        listing = data.get("data") or {}
        children = listing.get("children") or []
        return [_normalize(child.get("data") or {}) for child in children if child.get("data")]
    except Exception:
        return []


def _normalize(post: dict[str, Any]) -> dict[str, Any]:
    post_id = post.get("id", "")
    permalink = post.get("permalink", "")
    return {
        "id": post_id,
        "title": (post.get("title") or "")[:500],
        "author": post.get("author", "[deleted]"),
        "subreddit": post.get("subreddit", ""),
        "score": post.get("score", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.0),
        "num_comments": post.get("num_comments", 0),
        "url": post.get("url", ""),
        "domain": post.get("domain", ""),
        "is_self": post.get("is_self", False),
        "selftext": (post.get("selftext") or "")[:500],
        "created_utc": post.get("created_utc", 0),
        "over_18": post.get("over_18", False),
        "permalink": f"https://www.reddit.com{permalink}" if permalink else "",
        "flair": (post.get("link_flair_text") or "")[:100],
        "source_id": META["id"],
    }
