"""CCXT · 100+ 中心化交易所行情聚合 · 仅内部决策用途。

⚠️  重要合规声明：
  - 本模块调用 CCXT 库聚合 CEX 行情数据，数据来源各交易所官方 REST API。
  - redistribute: false — 禁止对外分发原始行情数据，仅供内部量化决策。
  - 须遵守各 CEX 的 Terms of Service（Binance/Bybit/OKX 等均明确限制商业再分发）。
  - 数据仅从公开端点获取（无账户/无私有权限），符合各 ToS 的只读公开访问条款。

🌐 注意：本模块需要能访问海外（被墙）交易所 API，Mac 环境可能超时，
   生产环境需在 probe-a（有独立公网 EIP + mihomo 代理）运行。

依赖安装：pip install ccxt
支持的主要交易所（免费公开行情）：
  binance, bybit, okx, coinbase, kraken, kucoin, gate, htx, mexc …（100+ 更多）
"""
from __future__ import annotations

from typing import Any

META: dict[str, Any] = {
    "id": "ccxt_src",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["crypto", "price", "ohlcv", "orderbook"],
    "redistribute": False,   # 🔴 禁止对外分发
}

_TIMEOUT_MS = 20_000   # ccxt 使用毫秒
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; internal-only)",
}


def configured() -> bool:
    """CCXT 无需全局 key（公开行情），恒返回 True；若 ccxt 未安装返回 False。"""
    try:
        import ccxt  # noqa: F401
        return True
    except ImportError:
        return False


def ticker(
    exchange_id: str,
    symbol: str,
) -> dict[str, Any]:
    """取单个交易所单个交易对的最新行情快照。

    Args:
        exchange_id: CCXT 交易所 id，如 "binance" / "bybit" / "okx" / "kraken"
        symbol:      交易对，如 "BTC/USDT" / "ETH/USDT" / "SOL/USDT"

    Returns:
        {"exchange", "symbol", "last", "bid", "ask", "high", "low",
         "volume", "quoteVolume", "timestamp", "source_id"}
        失败返回空 dict。

    合规：仅公开 ticker 端点，不含账户信息，无认证，符合各 CEX ToS。
    """
    try:
        import ccxt
        ExClass = getattr(ccxt, exchange_id, None)
        if ExClass is None:
            return {}
        ex = ExClass({"timeout": _TIMEOUT_MS})
        ex.headers.update(_HEADERS)  # type: ignore[attr-defined]
        t = ex.fetch_ticker(symbol)
        if not t:
            return {}
        return {
            "exchange": exchange_id,
            "symbol": symbol,
            "last": t.get("last"),
            "bid": t.get("bid"),
            "ask": t.get("ask"),
            "high": t.get("high"),
            "low": t.get("low"),
            "volume": t.get("baseVolume"),
            "quoteVolume": t.get("quoteVolume"),
            "percentage": t.get("percentage"),
            "timestamp": t.get("timestamp"),
            "datetime": t.get("datetime"),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def tickers(
    exchange_id: str,
    symbols: list[str] | None = None,
) -> list[dict[str, Any]]:
    """批量取行情快照。

    Args:
        exchange_id: 交易所 id
        symbols:     交易对列表；None = 全部（慎用，可能数千对）

    Returns:
        [ticker_dict, ...] 或空列表。
    """
    try:
        import ccxt
        ExClass = getattr(ccxt, exchange_id, None)
        if ExClass is None:
            return []
        ex = ExClass({"timeout": _TIMEOUT_MS})
        ex.headers.update(_HEADERS)  # type: ignore[attr-defined]
        raw: dict[str, Any] = ex.fetch_tickers(symbols or [])
        results: list[dict[str, Any]] = []
        for sym, t in raw.items():
            results.append({
                "exchange": exchange_id,
                "symbol": sym,
                "last": t.get("last"),
                "bid": t.get("bid"),
                "ask": t.get("ask"),
                "high": t.get("high"),
                "low": t.get("low"),
                "volume": t.get("baseVolume"),
                "quoteVolume": t.get("quoteVolume"),
                "percentage": t.get("percentage"),
                "timestamp": t.get("timestamp"),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def ohlcv(
    exchange_id: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """取 K 线数据（OHLCV）。

    Args:
        exchange_id: 交易所 id
        symbol:      交易对，如 "BTC/USDT"
        timeframe:   时间粒度，如 "1m" / "5m" / "1h" / "4h" / "1d"
        limit:       K 线条数（1-500）

    Returns:
        [{"timestamp", "open", "high", "low", "close", "volume", "source_id"}] 或空列表。
    """
    try:
        import ccxt
        ExClass = getattr(ccxt, exchange_id, None)
        if ExClass is None:
            return []
        ex = ExClass({"timeout": _TIMEOUT_MS})
        ex.headers.update(_HEADERS)  # type: ignore[attr-defined]
        raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=max(1, min(limit, 500)))
        results: list[dict[str, Any]] = []
        for bar in raw:
            results.append({
                "timestamp": bar[0],
                "open": bar[1],
                "high": bar[2],
                "low": bar[3],
                "close": bar[4],
                "volume": bar[5],
                "symbol": symbol,
                "exchange": exchange_id,
                "timeframe": timeframe,
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def exchanges() -> list[str]:
    """返回 CCXT 支持的全部交易所 id 列表（只读，无网络请求）。"""
    try:
        import ccxt
        return list(ccxt.exchanges)
    except Exception:
        return []
