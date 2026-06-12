"""CoinGecko · 加密货币行情与市场数据 · 无需 key（免费层）· 公开数据。

端点（免费层，无需 API Key）：
  coins_list    GET https://api.coingecko.com/api/v3/coins/list
  markets       GET https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd
  coin_detail   GET https://api.coingecko.com/api/v3/coins/{id}
  price         GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
  trending      GET https://api.coingecko.com/api/v3/search/trending
合规：CoinGecko 公开 API，免费层无需注册，官方 ToS 允许非商业和小规模商业读取行情数据。
速率限制：约 10-30 req/min（免费层），失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "coingecko",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["crypto", "price", "market"],
}

_API_BASE = "https://api.coingecko.com/api/v3"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def simple_price(
    coin_ids: list[str],
    vs_currencies: list[str] | None = None,
    include_24h_change: bool = True,
    include_market_cap: bool = False,
) -> dict[str, Any]:
    """取多个币种的实时价格。

    Args:
        coin_ids:           CoinGecko 币种 id 列表，如 ["bitcoin", "ethereum", "solana"]
        vs_currencies:      计价货币，如 ["usd", "cny"]；默认 ["usd"]
        include_24h_change: 是否含 24h 涨跌幅
        include_market_cap: 是否含市值

    Returns:
        {"bitcoin": {"usd": 65000, "usd_24h_change": 1.5}, ...}
        带 source_id 字段。失败返回空 dict。
    """
    if not coin_ids:
        return {}
    if vs_currencies is None:
        vs_currencies = ["usd"]
    params: dict[str, str] = {
        "ids": ",".join(coin_ids),
        "vs_currencies": ",".join(vs_currencies),
        "include_24hr_change": "true" if include_24h_change else "false",
        "include_market_cap": "true" if include_market_cap else "false",
    }
    try:
        r = httpx.get(f"{_API_BASE}/simple/price", params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        data["source_id"] = META["id"]
        return data
    except Exception:
        return {}


def markets(
    vs_currency: str = "usd",
    top_n: int = 20,
    category: str = "",
    order: str = "market_cap_desc",
) -> list[dict[str, Any]]:
    """取加密货币市场排行（按市值等排序）。

    Args:
        vs_currency: 计价货币，如 "usd" / "cny"
        top_n:       返回条数（1-250）
        category:    分类过滤，如 "decentralized-finance-defi" / "layer-1"；空 = 不过滤
        order:       排序方式，如 "market_cap_desc" / "volume_desc" / "price_change_percentage_24h_desc"

    Returns:
        [{"id", "symbol", "name", "current_price", "market_cap", "total_volume",
          "price_change_percentage_24h", "circulating_supply", "source_id"}] 或空列表。
    """
    params: dict[str, Any] = {
        "vs_currency": vs_currency,
        "order": order,
        "per_page": str(max(1, min(top_n, 250))),
        "page": "1",
        "sparkline": "false",
    }
    if category:
        params["category"] = category
    try:
        r = httpx.get(f"{_API_BASE}/coins/markets", params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        results: list[dict[str, Any]] = []
        for item in data:
            results.append(_normalize_market(item, vs_currency))
        return results
    except Exception:
        return []


def trending() -> list[dict[str, Any]]:
    """取 CoinGecko 当前趋势榜（24h 搜索量最高的前7个）。

    Returns:
        [{"id", "name", "symbol", "market_cap_rank", "score", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(f"{_API_BASE}/search/trending", headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        coins = data.get("coins") or []
        results: list[dict[str, Any]] = []
        for entry in coins:
            item = entry.get("item") or entry
            results.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "symbol": item.get("symbol", ""),
                "market_cap_rank": item.get("market_cap_rank"),
                "score": item.get("score"),
                "thumb": item.get("thumb", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def _normalize_market(item: dict[str, Any], vs_currency: str) -> dict[str, Any]:
    return {
        "id": item.get("id", ""),
        "symbol": item.get("symbol", ""),
        "name": item.get("name", ""),
        "current_price": item.get("current_price"),
        "market_cap": item.get("market_cap"),
        "market_cap_rank": item.get("market_cap_rank"),
        "total_volume": item.get("total_volume"),
        "price_change_24h": item.get("price_change_24h"),
        "price_change_pct_24h": item.get("price_change_percentage_24h"),
        "circulating_supply": item.get("circulating_supply"),
        "ath": item.get("ath"),
        "atl": item.get("atl"),
        "vs_currency": vs_currency,
        "source_id": META["id"],
    }
