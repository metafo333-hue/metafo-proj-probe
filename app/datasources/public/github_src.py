"""GitHub REST API v3 · 可选 GITHUB_TOKEN env · 免费。

无 token：60 req/h（匿名）
有 token：5000 req/h（个人 token）

端点：
  repo_info  GET /repos/{owner}/{repo}
  search     GET /search/repositories?q=...
合规：GitHub ToS § API Terms，只取公开元数据，不抓私有仓库。
失败返回空，不抛出。
"""
from __future__ import annotations

import os
import re
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "github_src",
    "domain": ["D12", "D5"],
    "access_type": "free_with_key",
    "kinds": ["repo", "search"],
}

_API_BASE = "https://api.github.com"
_TIMEOUT = 15


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "")
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _parse_owner_repo(url_or_slug: str) -> tuple[str, str] | None:
    """从 URL 或 'owner/repo' 解析出 (owner, repo)。"""
    pat = re.compile(r"github\.com/([^/]+)/([^/?#]+)")
    m = pat.search(url_or_slug)
    if m:
        return m.group(1), m.group(2).rstrip(".git")
    slug = url_or_slug.strip("/")
    parts = slug.split("/")
    if len(parts) == 2 and all(parts):
        return parts[0], parts[1]
    return None


def repo_info(url_or_slug: str) -> dict[str, Any]:
    """取仓库元数据。返回 {name, full_name, description, stars, forks, license, url} 或空 dict。"""
    parsed = _parse_owner_repo(url_or_slug)
    if not parsed:
        return {}
    owner, repo = parsed
    try:
        r = httpx.get(
            f"{_API_BASE}/repos/{owner}/{repo}",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            d = r.json()
            return {
                "name": d.get("name", ""),
                "full_name": d.get("full_name", ""),
                "description": (d.get("description") or "")[:300],
                "stars": d.get("stargazers_count", 0),
                "forks": d.get("forks_count", 0),
                "open_issues": d.get("open_issues_count", 0),
                "license": (d.get("license") or {}).get("spdx_id", ""),
                "language": d.get("language", ""),
                "url": d.get("html_url", ""),
                "pushed_at": d.get("pushed_at", ""),
                "source_id": META["id"],
            }
    except Exception:
        pass
    return {}


def search(query: str, max_results: int = 5, sort: str = "stars") -> list[dict[str, Any]]:
    """搜索公开仓库。每条：{name, full_name, description, stars, url}。失败返回空列表。"""
    params = {
        "q": query,
        "sort": sort,
        "per_page": str(min(max_results, 10)),
    }
    try:
        r = httpx.get(
            f"{_API_BASE}/search/repositories",
            params=params,
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            return [
                {
                    "name": item.get("name", ""),
                    "full_name": item.get("full_name", ""),
                    "description": (item.get("description") or "")[:200],
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                    "url": item.get("html_url", ""),
                    "source_id": META["id"],
                }
                for item in items
            ]
    except Exception:
        pass
    return []
