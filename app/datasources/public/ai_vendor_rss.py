"""AI 厂商 RSS 聚合 · D17 · 无需 key · 免费。

数据源（均经实测 HTTP 200 · 2026-06-12）：
  fetch_openai         OpenAI 官方博客 RSS  — https://openai.com/news/rss.xml
  fetch_huggingface    HuggingFace 博客 RSS — https://huggingface.co/blog/feed.xml
  fetch_google_ai      Google AI 博客 RSS   — https://blog.research.google/feeds/posts/default
  fetch_mistral        Mistral AI 新闻 RSS  — https://mistral.ai/rss.xml
  fetch_all            聚合以上全部源

实测备注：
  - Anthropic 官方未提供公开 RSS 端点（/feed / /rss 均 404），暂不接入。
  - Olshansk/rss-feeds 机器可读 JSON 文件路径 404（README 200，OPML 404），
    改为直接聚合各厂商官方 RSS。
  - GitHub release Atom（deepseek / ollama）可用但为 release 事件流，非公告流，
    归入 github_src 管线更合适，本模块专注 AI 公司博客/公告。

合规：RSS 均为各厂商官方公开出口，无限制，允许聚合消费。失败返回空，不抛出。
"""
from __future__ import annotations

import re
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "ai_vendor_rss",
    "domain": ["D17", "D12"],
    "access_type": "free",
    "method": ["W"],
    "kinds": ["ai_news", "vendor_blog", "release"],
}

_TIMEOUT = 30
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
}

# 官方 RSS 端点（实测 200）
_FEEDS: dict[str, dict[str, str]] = {
    "openai": {
        "url": "https://openai.com/news/rss.xml",
        "vendor": "OpenAI",
        "type": "rss",
    },
    "huggingface": {
        "url": "https://huggingface.co/blog/feed.xml",
        "vendor": "HuggingFace",
        "type": "rss",
    },
    "google_ai": {
        "url": "https://blog.research.google/feeds/posts/default",
        "vendor": "Google AI",
        "type": "atom",
    },
    "mistral": {
        "url": "https://mistral.ai/rss.xml",
        "vendor": "Mistral AI",
        "type": "rss",
    },
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_openai(top_n: int = 20) -> list[dict[str, Any]]:
    """拉取 OpenAI 官方博客 / 公告 RSS。"""
    return _fetch_feed("openai", top_n=top_n)


def fetch_huggingface(top_n: int = 20) -> list[dict[str, Any]]:
    """拉取 HuggingFace 官方博客 RSS。"""
    return _fetch_feed("huggingface", top_n=top_n)


def fetch_google_ai(top_n: int = 20) -> list[dict[str, Any]]:
    """拉取 Google AI Research 博客 Atom Feed。"""
    return _fetch_feed("google_ai", top_n=top_n)


def fetch_mistral(top_n: int = 20) -> list[dict[str, Any]]:
    """拉取 Mistral AI 新闻 RSS。"""
    return _fetch_feed("mistral", top_n=top_n)


def fetch_all(
    vendors: list[str] | None = None,
    top_n: int = 50,
    keyword: str = "",
) -> list[dict[str, Any]]:
    """聚合所有 AI 厂商 RSS，按 published 降序排列。

    Args:
        vendors:  指定厂商列表，如 ["openai", "huggingface"]；None = 全部
        top_n:    最多返回条数（1-500）
        keyword:  按标题 / 摘要关键词过滤（大小写不敏感）

    Returns:
        [{"vendor", "title", "url", "published", "summary", "tags",
          "source_id"}] 或空列表。
    """
    target_keys = vendors if vendors else list(_FEEDS.keys())
    all_items: list[dict[str, Any]] = []
    for key in target_keys:
        if key not in _FEEDS:
            continue
        items = _fetch_feed(key, top_n=200)
        all_items.extend(items)

    if keyword:
        kw = keyword.lower()
        all_items = [
            i for i in all_items
            if kw in i.get("title", "").lower() or kw in i.get("summary", "").lower()
        ]

    # 按 published 降序（字典序近似排序，ISO8601 格式）
    all_items.sort(key=lambda x: x.get("published", ""), reverse=True)
    return all_items[:max(1, min(top_n, 500))]


# ── 内部解析 ──────────────────────────────────────────────────────────────────

def _fetch_feed(key: str, top_n: int = 50) -> list[dict[str, Any]]:
    """拉取并解析单个 feed，失败返回空列表。"""
    feed_meta = _FEEDS.get(key)
    if not feed_meta:
        return []
    url = feed_meta["url"]
    vendor = feed_meta["vendor"]
    feed_type = feed_meta["type"]
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        xml = r.text
        if feed_type == "atom":
            items = _parse_atom(xml, vendor)
        else:
            items = _parse_rss(xml, vendor)
        return items[:max(1, min(top_n, 500))]
    except Exception:
        return []


def _clean(text: str) -> str:
    """去除 HTML 标签，截断至 400 字符。"""
    clean = re.sub(r"<[^>]+>", " ", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:400]


def _parse_rss(xml: str, vendor: str) -> list[dict[str, Any]]:
    """极简 RSS 解析（正则）：<item> 块提取 title/link/pubDate/description。"""
    items: list[dict[str, Any]] = []
    for block in re.findall(r"<item[^>]*>(.*?)</item>", xml, re.DOTALL):
        title_m = re.search(r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.DOTALL)
        link_m = re.search(r"<link[^>]*>\s*(https?://[^\s<]+)\s*</link>", block, re.DOTALL)
        pub_m = re.search(r"<pubDate[^>]*>(.*?)</pubDate>", block, re.DOTALL)
        desc_m = re.search(r"<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", block, re.DOTALL)
        tags_m = re.findall(r"<category[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</category>", block, re.DOTALL)
        items.append({
            "vendor": vendor,
            "title": _clean(title_m.group(1) if title_m else ""),
            "url": (link_m.group(1) if link_m else "").strip(),
            "published": (pub_m.group(1) if pub_m else "").strip()[:50],
            "summary": _clean(desc_m.group(1) if desc_m else ""),
            "tags": [_clean(t) for t in tags_m if t.strip()][:10],
            "source_id": META["id"],
        })
    return items


def _parse_atom(xml: str, vendor: str) -> list[dict[str, Any]]:
    """极简 Atom 解析（正则）：<entry> 块提取 title/link/updated/summary。"""
    items: list[dict[str, Any]] = []
    for block in re.findall(r"<entry[^>]*>(.*?)</entry>", xml, re.DOTALL):
        title_m = re.search(r"<title[^>]*>(.*?)</title>", block, re.DOTALL)
        link_m = re.search(r'<link[^>]+href=["\']([^"\']+)["\']', block)
        updated_m = re.search(r"<updated[^>]*>(.*?)</updated>", block, re.DOTALL)
        summary_m = re.search(r"<summary[^>]*>(.*?)</summary>", block, re.DOTALL)
        if not summary_m:
            summary_m = re.search(r"<content[^>]*>(.*?)</content>", block, re.DOTALL)
        items.append({
            "vendor": vendor,
            "title": _clean(title_m.group(1) if title_m else ""),
            "url": (link_m.group(1) if link_m else "").strip(),
            "published": (updated_m.group(1) if updated_m else "").strip()[:50],
            "summary": _clean(summary_m.group(1) if summary_m else ""),
            "tags": [],
            "source_id": META["id"],
        })
    return items
