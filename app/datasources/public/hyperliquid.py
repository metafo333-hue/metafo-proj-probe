"""Hyperliquid · 链上永续合约 DEX · 无需 key · 免费 · POST /info。

端点：
  POST https://api.hyperliquid.xyz/info
  Body: {"type": "meta"} / {"type": "allMids"} / {"type": "fundingHistory", "coin": "BTC", ...}
  Content-Type: application/json

合规：Hyperliquid 官方公开 REST API，无需注册，链上去中心化协议，数据完全公开。
注意：从国内 Mac 可能被墙；部署到 probe-a 走 mihomo 代理方可稳定访问。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "hyperliquid",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["perp", "funding_rate", "open_interest", "dex"],
}

_API_URL = "https://api.hyperliquid.xyz/info"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def _post(payload: dict[str, Any]) -> Any:
    """向 /info 发 POST 请求，失败返回 None。"""
    try:
        r = httpx.post(_API_URL, json=payload, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def meta() -> dict[str, Any]:
    """获取所有可交易永续合约元信息（币种列表、杠杆、tick size 等）。

    Returns:
        {"universe": [...], "source_id"} 或空 dict。
        universe 每项: {"name", "szDecimals", "maxLeverage", ...}
    """
    data = _post({"type": "meta"})
    if not isinstance(data, dict):
        return {}
    universe = data.get("universe") or []
    return {
        "universe": universe[:200],  # 截断防超大
        "coin_count": len(universe),
        "source_id": META["id"],
    }


def all_mids() -> dict[str, float]:
    """获取所有永续合约当前中间价（mid price）。

    Returns:
        {"BTC": 67500.0, "ETH": 3500.0, ...} 或空 dict。
    """
    data = _post({"type": "allMids"})
    if not isinstance(data, dict):
        return {}
    result: dict[str, float] = {}
    for coin, price_str in data.items():
        try:
            result[coin] = float(price_str)
        except (ValueError, TypeError):
            result[coin] = 0.0
    return result


def funding_history(
    coin: str = "BTC",
    start_time: int | None = None,
    end_time: int | None = None,
) -> list[dict[str, Any]]:
    """获取某币种永续合约资金费率历史。

    Args:
        coin:       币种名，如 "BTC" / "ETH" / "SOL"
        start_time: 起始时间戳（毫秒）；None 则返回最近数据
        end_time:   结束时间戳（毫秒）；None 则为当前

    Returns:
        [{"coin", "funding_rate", "premium", "time", "source_id"}] 或空列表。
    """
    payload: dict[str, Any] = {"type": "fundingHistory", "coin": coin.upper()}
    if start_time is not None:
        payload["startTime"] = start_time
    if end_time is not None:
        payload["endTime"] = end_time

    data = _post(payload)
    if not isinstance(data, list):
        return []
    results: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        results.append({
            "coin": coin.upper(),
            "funding_rate": item.get("fundingRate", ""),
            "premium": item.get("premium", ""),
            "time": item.get("time"),
            "source_id": META["id"],
        })
    return results


def open_interest_by_coin(coin: str = "BTC") -> dict[str, Any]:
    """获取某币种全局未平仓合约（通过 clearinghouseState 汇总）。

    注意：Hyperliquid 公开 API 目前无直接全局 OI 端点，
    此函数通过 metaAndAssetCtxs 获取每个资产的上下文信息（含 OI）。

    Returns:
        {"coin", "open_interest", "funding_rate", "mark_price", "source_id"} 或空 dict。
    """
    data = _post({"type": "metaAndAssetCtxs"})
    if not isinstance(data, list) or len(data) < 2:
        return {}
    universe: list[dict[str, Any]] = data[0].get("universe") or []
    asset_ctxs: list[dict[str, Any]] = data[1] if isinstance(data[1], list) else []

    for i, asset in enumerate(universe):
        if asset.get("name", "").upper() == coin.upper():
            if i < len(asset_ctxs):
                ctx = asset_ctxs[i]
                return {
                    "coin": coin.upper(),
                    "open_interest": ctx.get("openInterest", ""),
                    "funding_rate": ctx.get("funding", ""),
                    "mark_price": ctx.get("markPx", ""),
                    "oracle_price": ctx.get("oraclePx", ""),
                    "source_id": META["id"],
                }
    return {}
