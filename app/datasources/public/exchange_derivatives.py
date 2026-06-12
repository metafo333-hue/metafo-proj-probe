"""交易所衍生品数据 · 资金费率 / 未平仓合约 · 无需 key · 免费公开 API。

端点（三大交易所官方 REST）：
  Binance FAPI
    funding_rate  GET https://fapi.binance.com/fapi/v1/fundingRate
    open_interest GET https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT
    ticker        GET https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT
  Bybit
    funding_rate  GET https://api.bybit.com/v5/market/funding/history
    open_interest GET https://api.bybit.com/v5/market/open-interest
  OKX
    funding_rate  GET https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP
    open_interest GET https://www.okx.com/api/v5/public/open-interest?instType=SWAP

合规：均为交易所官方公开 REST API，无需注册，无 ToS 商业限制（行情数据开放）。
注意：从国内 Mac 可能被墙；部署到 probe-a 走 mihomo 代理方可稳定访问。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "exchange_derivatives",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["funding_rate", "open_interest", "derivatives"],
}

_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}

# Binance FAPI base
_BINANCE_FAPI = "https://fapi.binance.com/fapi/v1"
# Bybit v5
_BYBIT_BASE = "https://api.bybit.com/v5/market"
# OKX v5
_OKX_BASE = "https://www.okx.com/api/v5/public"


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


# ── Binance FAPI ────────────────────────────────────────────────────────────

def binance_funding_rate(symbol: str = "BTCUSDT", limit: int = 10) -> list[dict[str, Any]]:
    """Binance 永续合约资金费率历史。

    Args:
        symbol: 合约代码，如 "BTCUSDT" / "ETHUSDT"
        limit:  返回条数（1-1000）

    Returns:
        [{"exchange", "symbol", "funding_rate", "funding_time", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_BINANCE_FAPI}/fundingRate",
            params={"symbol": symbol.upper(), "limit": max(1, min(limit, 1000))},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        return [
            {
                "exchange": "binance",
                "symbol": item.get("symbol", ""),
                "funding_rate": float(item.get("fundingRate", 0)),
                "funding_time": item.get("fundingTime"),
                "source_id": META["id"],
            }
            for item in data
        ]
    except Exception:
        return []


def binance_open_interest(symbol: str = "BTCUSDT") -> dict[str, Any]:
    """Binance 永续合约当前未平仓合约量。

    Returns:
        {"exchange", "symbol", "open_interest", "time", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_BINANCE_FAPI}/openInterest",
            params={"symbol": symbol.upper()},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return {
            "exchange": "binance",
            "symbol": data.get("symbol", ""),
            "open_interest": float(data.get("openInterest", 0)),
            "time": data.get("time"),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def binance_ticker_24hr(symbol: str = "BTCUSDT") -> dict[str, Any]:
    """Binance 永续合约 24 小时行情摘要。

    Returns:
        {"exchange", "symbol", "last_price", "volume", "price_change_pct", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_BINANCE_FAPI}/ticker/24hr",
            params={"symbol": symbol.upper()},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return {
            "exchange": "binance",
            "symbol": data.get("symbol", ""),
            "last_price": float(data.get("lastPrice", 0)),
            "volume": float(data.get("volume", 0)),
            "quote_volume": float(data.get("quoteVolume", 0)),
            "price_change_pct": float(data.get("priceChangePercent", 0)),
            "source_id": META["id"],
        }
    except Exception:
        return {}


# ── Bybit ────────────────────────────────────────────────────────────────────

def bybit_funding_rate(symbol: str = "BTCUSDT", limit: int = 10) -> list[dict[str, Any]]:
    """Bybit 永续合约资金费率历史。

    Args:
        symbol: 合约代码，如 "BTCUSDT"
        limit:  返回条数（1-200）

    Returns:
        [{"exchange", "symbol", "funding_rate", "funding_rate_timestamp", "source_id"}]。
    """
    try:
        r = httpx.get(
            f"{_BYBIT_BASE}/funding/history",
            params={"category": "linear", "symbol": symbol.upper(), "limit": max(1, min(limit, 200))},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = (data.get("result") or {}).get("list") or []
        return [
            {
                "exchange": "bybit",
                "symbol": item.get("symbol", ""),
                "funding_rate": item.get("fundingRate", ""),
                "funding_rate_timestamp": item.get("fundingRateTimestamp", ""),
                "source_id": META["id"],
            }
            for item in items
        ]
    except Exception:
        return []


def bybit_open_interest(symbol: str = "BTCUSDT", interval_time: str = "1h", limit: int = 10) -> list[dict[str, Any]]:
    """Bybit 永续合约未平仓合约历史。

    Args:
        symbol:        合约代码
        interval_time: 时间粒度，"5min"/"15min"/"30min"/"1h"/"4h"/"1d"
        limit:         返回条数

    Returns:
        [{"exchange", "symbol", "open_interest_value", "timestamp", "source_id"}]。
    """
    try:
        r = httpx.get(
            f"{_BYBIT_BASE}/open-interest",
            params={
                "category": "linear",
                "symbol": symbol.upper(),
                "intervalTime": interval_time,
                "limit": max(1, min(limit, 200)),
            },
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = (data.get("result") or {}).get("list") or []
        return [
            {
                "exchange": "bybit",
                "symbol": symbol.upper(),
                "open_interest_value": item.get("openInterestValue", ""),
                "timestamp": item.get("timestamp", ""),
                "source_id": META["id"],
            }
            for item in items
        ]
    except Exception:
        return []


# ── OKX ─────────────────────────────────────────────────────────────────────

def okx_funding_rate(inst_id: str = "BTC-USDT-SWAP") -> dict[str, Any]:
    """OKX 永续合约当前资金费率。

    Args:
        inst_id: 产品 ID，如 "BTC-USDT-SWAP" / "ETH-USDT-SWAP"

    Returns:
        {"exchange", "inst_id", "funding_rate", "next_funding_time", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_OKX_BASE}/funding-rate",
            params={"instId": inst_id},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        items = data.get("data") or []
        if not items:
            return {}
        item = items[0]
        return {
            "exchange": "okx",
            "inst_id": item.get("instId", ""),
            "funding_rate": item.get("fundingRate", ""),
            "next_funding_time": item.get("nextFundingTime", ""),
            "realized_rate": item.get("realizedRate", ""),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def okx_open_interest(inst_type: str = "SWAP", inst_id: str = "BTC-USDT-SWAP") -> list[dict[str, Any]]:
    """OKX 永续合约未平仓合约。

    Args:
        inst_type: 产品类型，"SWAP" / "FUTURES" / "OPTION"
        inst_id:   产品 ID（可选，留空则返回全部）

    Returns:
        [{"exchange", "inst_id", "oi", "oi_ccy", "ts", "source_id"}]。
    """
    try:
        params: dict[str, str] = {"instType": inst_type}
        if inst_id:
            params["instId"] = inst_id
        r = httpx.get(
            f"{_OKX_BASE}/open-interest",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or []
        return [
            {
                "exchange": "okx",
                "inst_id": item.get("instId", ""),
                "oi": item.get("oi", ""),
                "oi_ccy": item.get("oiCcy", ""),
                "ts": item.get("ts", ""),
                "source_id": META["id"],
            }
            for item in items
        ]
    except Exception:
        return []
