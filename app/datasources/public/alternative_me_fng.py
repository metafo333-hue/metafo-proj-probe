"""Alternative.me 恐慌与贪婪指数 · 无需 key · 完全免费 · 公开 API。

端点：
  GET https://api.alternative.me/fng/?limit=10&format=json
  支持参数：limit（条数 1-365）· date_format（unix/us/cn/kr/world）

合规：Alternative.me 公开 API，官方明确免费使用，无需注册，无商业限制。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "alternative_me_fng",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["sentiment", "fear_greed_index", "crypto"],
}

_API_BASE = "https://api.alternative.me"
_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}

# 指数分类映射
_VALUE_CLASS = {
    (0, 24): "Extreme Fear",
    (25, 44): "Fear",
    (45, 55): "Neutral",
    (56, 74): "Greed",
    (75, 100): "Extreme Greed",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def latest(limit: int = 1) -> list[dict[str, Any]]:
    """获取最新恐慌贪婪指数。

    Args:
        limit: 返回条数（1-365；1=今日）

    Returns:
        [{"value", "value_classification", "timestamp", "time_until_update", "source_id"}]
        或空列表。
    """
    try:
        r = httpx.get(
            f"{_API_BASE}/fng/",
            params={"limit": max(1, min(limit, 365)), "format": "json"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or []
        if not isinstance(items, list):
            return []
        return [_normalize(item) for item in items]
    except Exception:
        return []


def history(days: int = 30) -> list[dict[str, Any]]:
    """获取指定天数的历史恐慌贪婪指数。

    Args:
        days: 历史天数（1-365）

    Returns:
        [{"value", "value_classification", "timestamp", "source_id"}] 或空列表，按时间倒序。
    """
    return latest(limit=days)


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    try:
        val = int(item.get("value", 0))
    except (ValueError, TypeError):
        val = 0
    classification = item.get("value_classification", "")
    # 如 API 未返回分类则自行补
    if not classification:
        for (lo, hi), label in _VALUE_CLASS.items():
            if lo <= val <= hi:
                classification = label
                break
    return {
        "value": val,
        "value_classification": classification,
        "timestamp": item.get("timestamp", ""),
        "time_until_update": item.get("time_until_update"),
        "source_id": META["id"],
    }
