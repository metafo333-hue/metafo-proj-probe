"""sanctions.network · 开放制裁数据 API（多来源整合 · PostgREST）。

端点（已验证 · 基于 https://api.sanctions.network）：
  GET /sanctions              — 直接查询制裁表（PostgREST 过滤参数）
  GET /rpc/search_sanctions   — 触发相似度全文搜索（name= 参数 · 支持拼写变体）

合规：sanctions.network 是 Arsh Singh 维护的开放数据项目（MIT/开放许可）。
      数据来源：OFAC / UN / EU / UK / 其他官方制裁名单（均为公有领域数据）。
      官网明确声明：「The API … is free to use, for any use case.」
      GitHub：https://github.com/arshsingh/sanctions
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "sanctions_network",
    "domain": ["D8"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["sanctions", "compliance", "entity"],
}

_API_BASE = "https://api.sanctions.network"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; compliance-research)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search(
    name: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """触发相似度全文搜索（支持拼写变体，如 Alexei vs Alexey）。

    使用 /rpc/search_sanctions 端点（postgREST RPC），基于 trigram 相似度匹配。

    Args:
        name:  搜索词（姓名/实体名·支持拼写变体）
        limit: 返回条数（1-100）

    Returns:
        [{"names", "source", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_API_BASE}/rpc/search_sanctions",
            params={"name": name, "limit": str(max(1, min(limit, 100)))},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        body = r.json()
        if not isinstance(body, list):
            return []
        return [_normalize(item) for item in body[:max(1, min(limit, 100))]]
    except Exception:
        return []


def query_sanctions(
    source_id: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """直接查询制裁表（PostgREST 风格过滤）。

    Args:
        source_id: 制裁来源过滤，如 "ofac" / "unsc" / "eu" / "uk"；空 = 不限
        limit:     返回条数（1-100）
        offset:    分页偏移

    Returns:
        [{"names", "source", "source_id"}] 或空列表。
    """
    params: dict[str, str] = {
        "limit": str(max(1, min(limit, 100))),
        "offset": str(max(0, offset)),
    }
    if source_id:
        params["source_id"] = f"eq.{source_id}"
    try:
        r = httpx.get(
            f"{_API_BASE}/sanctions",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        body = r.json()
        if not isinstance(body, list):
            return []
        return [_normalize(item) for item in body]
    except Exception:
        return []


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    """标准化 sanctions.network 条目（schema: names[], source, positions, remarks）。"""
    return {
        "names": item.get("names") or [],
        "source": item.get("source", ""),
        "positions": item.get("positions") or [],
        "remarks": (item.get("remarks") or "")[:300],
        "source_id": META["id"],
    }
