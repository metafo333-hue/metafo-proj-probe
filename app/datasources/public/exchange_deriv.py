"""交易所衍生品官方 REST · 资金费率 + 持仓量（OI）。

数据源：Binance / Bybit / OKX 官方合约 REST API（免费·无需 key）
端点：
  Binance  GET https://fapi.binance.com/fapi/v1/fundingRate        — 资金费率历史
  Binance  GET https://fapi.binance.com/fapi/v1/openInterest       — 合约持仓量
  Bybit    GET https://api.bybit.com/v5/market/funding/history      — 资金费率历史
  Bybit    GET https://api.bybit.com/v5/market/open-interest        — 持仓量
  OKX      GET https://www.okx.com/api/v5/public/funding-rate      — 当前资金费率
  OKX      GET https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume/ratio — OI
合规：均为各平台官方公开 REST 端点，公开行情数据，无认证要求，不含账户信息。

🌐 注意：Binance/Bybit/OKX 均在中国大陆被封锁，Mac 直连可能超时，
   生产环境需在 probe-a（有代理）运行。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "exchange_deriv",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["funding_rate", "open_interest", "derivatives"],
}

_TIMEOUT = 20


def configured() -> bool:
    """无需 key，恒返回 True（各端点无认证）。"""
    return True
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}

# ── Binance ─────────────────────────────────────────────────────────────────
_BINANCE_FAPI = "https://fapi.binance.com/fapi/v1"


def binance_funding_rate(
    symbol: str = "BTCUSDT",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """取 Binance 合约资金费率历史。

    Args:
        symbol: 合约 symbol，如 "BTCUSDT" / "ETHUSDT"
        limit:  返回条数（1-1000）

    Returns:
        [{"exchange", "symbol", "funding_rate", "funding_time", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_BINANCE_FAPI}/fundingRate",
            params={"symbol": symbol, "limit": str(max(1, min(limit, 1000)))},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
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
    """取 Binance 合约当前持仓量（OI）。

    Returns:
        {"exchange", "symbol", "open_interest", "time", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_BINANCE_FAPI}/openInterest",
            params={"symbol": symbol},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        return {
            "exchange": "binance",
            "symbol": data.get("symbol", ""),
            "open_interest": float(data.get("openInterest", 0)),
            "time": data.get("time"),
            "source_id": META["id"],
        }
    except Exception:
        return {}


# ── Bybit ────────────────────────────────────────────────────────────────────
_BYBIT_BASE = "https://api.bybit.com/v5/market"


def bybit_funding_rate(
    symbol: str = "BTCUSDT",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """取 Bybit 合约资金费率历史。

    Args:
        symbol: 合约 symbol，如 "BTCUSDT"
        limit:  条数（1-200）

    Returns:
        [{"exchange", "symbol", "funding_rate", "funding_rate_timestamp", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_BYBIT_BASE}/funding/history",
            params={"symbol": symbol, "limit": str(max(1, min(limit, 200)))},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        body = r.json()
        items = (body.get("result") or {}).get("list") or []
        return [
            {
                "exchange": "bybit",
                "symbol": item.get("symbol", ""),
                "funding_rate": float(item.get("fundingRate", 0)),
                "funding_rate_timestamp": item.get("fundingRateTimestamp"),
                "source_id": META["id"],
            }
            for item in items
        ]
    except Exception:
        return []


def bybit_open_interest(
    symbol: str = "BTCUSDT",
    interval_time: str = "1h",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """取 Bybit 合约持仓量（OI）历史。

    Args:
        symbol:        合约 symbol
        interval_time: 粒度 "5min" / "15min" / "30min" / "1h" / "4h" / "1d"
        limit:         条数（1-200）

    Returns:
        [{"exchange", "symbol", "oi", "oi_value", "timestamp", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_BYBIT_BASE}/open-interest",
            params={
                "symbol": symbol,
                "intervalTime": interval_time,
                "limit": str(max(1, min(limit, 200))),
                "category": "linear",
            },
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        body = r.json()
        items = (body.get("result") or {}).get("list") or []
        return [
            {
                "exchange": "bybit",
                "symbol": symbol,
                "oi": item.get("openInterest"),
                "oi_value": item.get("openInterestValue"),
                "timestamp": item.get("timestamp"),
                "source_id": META["id"],
            }
            for item in items
        ]
    except Exception:
        return []


# ── OKX ─────────────────────────────────────────────────────────────────────
_OKX_BASE = "https://www.okx.com/api/v5"


def okx_funding_rate(inst_id: str = "BTC-USDT-SWAP") -> dict[str, Any]:
    """取 OKX 合约当前资金费率。

    Args:
        inst_id: OKX 合约 ID，如 "BTC-USDT-SWAP" / "ETH-USDT-SWAP"

    Returns:
        {"exchange", "inst_id", "funding_rate", "next_funding_rate",
         "funding_time", "next_funding_time", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_OKX_BASE}/public/funding-rate",
            params={"instId": inst_id},
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
            "exchange": "okx",
            "inst_id": item.get("instId", ""),
            "funding_rate": float(item.get("fundingRate", 0)),
            "next_funding_rate": item.get("nextFundingRate"),
            "funding_time": item.get("fundingTime"),
            "next_funding_time": item.get("nextFundingTime"),
            "source_id": META["id"],
        }
    except Exception:
        return {}
