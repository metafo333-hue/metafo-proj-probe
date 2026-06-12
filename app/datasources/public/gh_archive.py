"""GH Archive · GitHub 公开事件归档 · 免费 · 无需 key · D12。

端点（HTTP GET）：
  https://data.gharchive.org/YYYY-MM-DD-H.json.gz
  每小时一个 gzip 压缩 JSONL 文件，每行是一个 GitHub 事件。
合规：GH Archive 由 Ilya Grigorik 维护，数据来源于 GitHub Events API 公开数据，
      CC0 公有领域授权，官方明确允许商业与研究使用。
注意：单文件 ~60-100 MB（压缩后 ~5-10 MB），不可达/限速时返回空，不抛出。
"""
from __future__ import annotations

import gzip
import io
import json
from datetime import datetime, timezone
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "gh_archive",
    "domain": ["D12"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["event", "push", "pr", "release", "star"],
}

_BASE_URL = "https://data.gharchive.org"
_TIMEOUT = 60  # 文件较大，延长超时
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/gzip, */*",
}

# 支持的事件类型
EVENT_TYPES = (
    "PushEvent",
    "PullRequestEvent",
    "IssuesEvent",
    "WatchEvent",
    "ForkEvent",
    "ReleaseEvent",
    "CreateEvent",
    "DeleteEvent",
    "IssueCommentEvent",
    "PullRequestReviewEvent",
)


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_hour(
    year: int,
    month: int,
    day: int,
    hour: int,
    event_types: list[str] | None = None,
    max_events: int = 500,
    repo_filter: str = "",
) -> list[dict[str, Any]]:
    """下载并解析特定小时的 GitHub 事件归档。

    Args:
        year, month, day, hour: 目标时间（UTC），hour 0-23
        event_types:  过滤事件类型列表，如 ["PushEvent", "PullRequestEvent"]；
                      None 或空列表表示返回所有类型
        max_events:   最多返回条数（防止单文件过大撑爆内存），默认 500
        repo_filter:  仓库名关键词过滤（包含即保留），空字符串表示不过滤

    Returns:
        [{"type", "repo", "actor", "created_at", "payload_summary", "source_id"}]
        或空列表。
    """
    fname = f"{year}-{month:02d}-{day:02d}-{hour}.json.gz"
    url = f"{_BASE_URL}/{fname}"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        raw_gz = r.content
        with gzip.open(io.BytesIO(raw_gz), "rt", encoding="utf-8", errors="replace") as f:
            results: list[dict[str, Any]] = []
            for line in f:
                if len(results) >= max_events:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                evt_type = evt.get("type", "")
                # 事件类型过滤
                if event_types and evt_type not in event_types:
                    continue
                repo_name = evt.get("repo", {}).get("name", "")
                # 仓库名过滤
                if repo_filter and repo_filter.lower() not in repo_name.lower():
                    continue
                results.append(_normalize(evt))
            return results
    except Exception:
        return []


def fetch_recent(
    hours_back: int = 1,
    event_types: list[str] | None = None,
    max_events: int = 200,
    repo_filter: str = "",
) -> list[dict[str, Any]]:
    """获取最近 N 小时前的 GitHub 事件（往前推避免文件尚未生成）。

    Args:
        hours_back:  往回推几个小时（默认 1，即前一小时的完整数据）
        event_types: 过滤事件类型
        max_events:  最多返回条数
        repo_filter: 仓库名关键词过滤

    Returns:
        [{"type", "repo", "actor", "created_at", "payload_summary", "source_id"}]
        或空列表。
    """
    now = datetime.now(tz=timezone.utc)
    # 往回推 hours_back 小时，避免最新文件还没生成
    import math
    from datetime import timedelta
    target = now - timedelta(hours=max(1, hours_back))
    return fetch_hour(
        year=target.year,
        month=target.month,
        day=target.day,
        hour=target.hour,
        event_types=event_types,
        max_events=max_events,
        repo_filter=repo_filter,
    )


def _normalize(evt: dict[str, Any]) -> dict[str, Any]:
    repo = evt.get("repo") or {}
    actor = evt.get("actor") or {}
    org = evt.get("org") or {}
    payload = evt.get("payload") or {}
    evt_type = evt.get("type", "")

    # 按事件类型提取摘要
    payload_summary: dict[str, Any] = {}
    if evt_type == "PushEvent":
        payload_summary = {
            "ref": payload.get("ref", ""),
            "commits_count": payload.get("size", 0),
            "distinct_commits": payload.get("distinct_size", 0),
        }
    elif evt_type == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        payload_summary = {
            "action": payload.get("action", ""),
            "title": (pr.get("title") or "")[:200],
            "state": pr.get("state", ""),
            "merged": pr.get("merged", False),
        }
    elif evt_type in ("IssuesEvent", "IssueCommentEvent"):
        issue = payload.get("issue") or {}
        payload_summary = {
            "action": payload.get("action", ""),
            "title": (issue.get("title") or "")[:200],
            "state": issue.get("state", ""),
        }
    elif evt_type == "WatchEvent":
        payload_summary = {"action": payload.get("action", "starred")}
    elif evt_type == "ReleaseEvent":
        release = payload.get("release") or {}
        payload_summary = {
            "action": payload.get("action", ""),
            "tag": release.get("tag_name", ""),
            "name": (release.get("name") or "")[:200],
        }
    elif evt_type == "ForkEvent":
        forkee = payload.get("forkee") or {}
        payload_summary = {"forkee": forkee.get("full_name", "")}

    return {
        "type": evt_type,
        "repo": repo.get("name", ""),
        "repo_url": f"https://github.com/{repo.get('name', '')}",
        "actor": actor.get("login", ""),
        "org": org.get("login", ""),
        "created_at": evt.get("created_at", ""),
        "public": evt.get("public", True),
        "payload_summary": payload_summary,
        "source_id": META["id"],
    }
