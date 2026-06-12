"""OSSInsight · 开源项目大数据分析 · 无需 key · 免费层。

端点（实测可用）：
  repo_info       GET https://api.ossinsight.io/gh/repo/{owner}/{repo}   — 仓库详情（含 stars/forks 等）
  github_search   GET https://api.github.com/search/repositories?q=...  — 热门仓库搜索（GitHub 公开 API）
  NOTE: v1/* 端点（/v1/repos/ /v1/trending/）已于 2026-06 返回 500，改用 /gh/ 路径。
合规：OSSInsight 是 PingCAP 开源项目，/gh/ 端点公开无需注册；GitHub 搜索 API 匿名 10 req/min。
数据来源 GitHub，遵循 GitHub ToS 使用范围。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "ossinsight",
    "domain": ["D12"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["repo", "developer", "trending"],
}

_API_BASE = "https://api.ossinsight.io"
_GH_SEARCH = "https://api.github.com/search/repositories"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def repo_summary(owner: str, repo: str) -> dict[str, Any]:
    """取 GitHub 仓库概要统计（通过 OSSInsight /gh/repo/ 端点）。

    Args:
        owner: 仓库 owner，如 "vuejs" / "facebook"
        repo:  仓库名，如 "vue" / "react"

    Returns:
        {"full_name", "stars", "forks", "watchers", "last_pushed",
         "language", "description", "source_id"} 或空 dict。
    """
    url = f"{_API_BASE}/gh/repo/{owner}/{repo}"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        # /gh/repo/ 返回结构：{"data": {...}}
        payload = data.get("data") if isinstance(data, dict) and "data" in data else data
        if not isinstance(payload, dict):
            return {}
        return _normalize_repo(payload, owner, repo)
    except Exception:
        return {}


def repo_star_history(
    owner: str,
    repo: str,
    period: str = "past_12_months",
) -> list[dict[str, Any]]:
    """取仓库 Star 增长趋势（通过 OSSInsight /gh/repo/ 端点获取基础信息）。

    Args:
        owner:  仓库 owner
        repo:   仓库名
        period: 保留参数（当前返回仓库概要，详细趋势数据需 OSSInsight v1 恢复）

    Returns:
        包含仓库基础信息的单条记录列表，或空列表。
    """
    # OSSInsight v1/trends 端点 2026-06 已失效，降级为仓库概要
    summary = repo_summary(owner, repo)
    if not summary:
        return []
    return [{"full_name": summary.get("full_name", ""), "stars": summary.get("stars"),
             "note": "trend endpoint unavailable, returning current summary",
             "source_id": META["id"]}]


def trending_repos(
    period: str = "past_28_days",
    language: str = "",
    top_n: int = 20,
) -> list[dict[str, Any]]:
    """取热门仓库排行（使用 GitHub Search API，匿名 10 req/min）。

    Args:
        period:   保留参数（当前按 stars 排序，不按时间段）
        language: 编程语言过滤，如 "Python" / "TypeScript"；空 = 不限
        top_n:    返回条数（1-30，超过 GitHub 匿名限制会降级为 10）

    Returns:
        [{"full_name", "description", "stars", "forks", "language", "source_id"}] 或空列表。
    """
    # GitHub 搜索 API：匿名 10 req/min，取 stars 最多的仓库
    q = "stars:>1000"
    if language:
        q += f" language:{language}"
    params: dict[str, Any] = {
        "q": q,
        "sort": "stars",
        "order": "desc",
        "per_page": str(max(1, min(top_n, 30))),
    }
    try:
        r = httpx.get(_GH_SEARCH, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("items") or []
        results: list[dict[str, Any]] = []
        for row in items[:top_n]:
            if not isinstance(row, dict):
                continue
            full_name = row.get("full_name", "")
            parts = full_name.split("/")
            results.append({
                "full_name": full_name,
                "owner": parts[0] if len(parts) > 1 else "",
                "repo": parts[1] if len(parts) > 1 else full_name,
                "description": (row.get("description") or "")[:300],
                "stars": row.get("stargazers_count"),
                "forks": row.get("forks_count"),
                "language": row.get("language", ""),
                "topics": row.get("topics", []),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def _normalize_repo(data: dict[str, Any], owner: str, repo: str) -> dict[str, Any]:
    return {
        "full_name": f"{owner}/{repo}",
        "owner": owner,
        "repo": repo,
        "description": (data.get("description") or "")[:300],
        "stars": data.get("stargazers_count") or data.get("stars"),
        "forks": data.get("forks_count") or data.get("forks"),
        "watchers": data.get("watchers_count") or data.get("watchers"),
        "contributors": data.get("contributors"),
        "language": data.get("language", ""),
        "last_pushed": data.get("pushed_at") or data.get("last_pushed", ""),
        "created_at": data.get("created_at", ""),
        "open_issues": data.get("open_issues_count") or data.get("open_issues"),
        "license": (data.get("license") or {}).get("spdx_id", "") if isinstance(data.get("license"), dict) else str(data.get("license", "")),
        "source_id": META["id"],
    }
