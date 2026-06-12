"""Alternative.me · 加密货币恐慌贪婪指数（Fear & Greed Index）。

端点：GET https://api.alternative.me/fng/
  参数：
    limit  — 历史条数（1-∞）；0 = 返回所有历史数据
    format — 返回格式（json · 默认）
合规：Alternative.me 公开 API，无需认证，官方明确免费开放使用。

该指数综合多维度市场情绪（波动率/市场动量/社媒情绪/调查/主导地位/趋势）
生成 0-100 分：0=极度恐慌，100=极度贪婪。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "alt_fng",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["sentiment", "fear_greed", "crypto"],
}

_API_URL = "https://api.alternative.me/fng/"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def latest() -> dict[str, Any]:
    """取最新一条恐慌贪婪指数。

    Returns:
        {"value", "value_classification", "timestamp", "time_until_update", "source_id"}
        失败返回空 dict。
    """
    try:
        r = httpx.get(
            _API_URL,
            params={"limit": "1", "format": "json"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        body = r.json()
        data = body.get("data") or []
        if not data:
            return {}
        item = data[0]
        return {
            "value": int(item.get("value", 0)),
            "value_classification": item.get("value_classification", ""),
            "timestamp": int(item.get("timestamp", 0)),
            "time_until_update": item.get("time_until_update"),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def history(limit: int = 30) -> list[dict[str, Any]]:
    """取历史恐慌贪婪指数序列。

    Args:
        limit: 历史条数（1-∞；0 = 全量历史，约数千条，请谨慎）

    Returns:
        [{"value", "value_classification", "timestamp", "source_id"}] 或空列表。
        最新一条在 index 0。
    """
    try:
        r = httpx.get(
            _API_URL,
            params={"limit": str(max(0, limit)), "format": "json"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        body = r.json()
        data = body.get("data") or []
        return [
            {
                "value": int(item.get("value", 0)),
                "value_classification": item.get("value_classification", ""),
                "timestamp": int(item.get("timestamp", 0)),
                "source_id": META["id"],
            }
            for item in data
        ]
    except Exception:
        return []
